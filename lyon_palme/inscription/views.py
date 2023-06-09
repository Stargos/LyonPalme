from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse

from .regex import Regex
from .forms import Formulaire_inscription, LoginForm
from .models import Inscription,Archive

@login_required
def inscription_form(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            form = Formulaire_inscription(request.POST)
            if form.is_valid() and Regex.verif_mail(form.cleaned_data['mail']) and Regex.verif_tel(form.cleaned_data['telephone']) and Regex.verif_cp(form.cleaned_data['code_postal']):
                reussi = "Utilisateur ajouté avec succès"
                
                login = request.POST['prenom'][0]+request.POST['nom']
                mdp = request.POST['date_naissance']
                mail = request.POST['mail']

                utilisateur = User.objects.create_user(login, mail, mdp)
                utilisateur.save()
                
                adherent = Inscription()
                adherent.user = utilisateur
                adherent.nom = request.POST['nom']
                adherent.prenom = request.POST['prenom']
                adherent.date_inscription = timezone.now()
                adherent.date_naissance = request.POST['date_naissance']
                adherent.mail = request.POST['mail']
                adherent.telephone = request.POST['telephone']
                adherent.adresse = request.POST['adresse']
                adherent.code_postal = request.POST['code_postal']
                adherent.date_certificat = request.POST['date_certificat']
                adherent.affiche_trombinoscope = request.POST.get('trombinoscope',False)
                adherent.affiche_annuaire = request.POST.get('annuaire',False)
                adherent.cotisation = request.POST.get('cotisation', False)
                adherent.save()

                return render(request, 'inscription/inscription_form.html', {'form' : form, 'reussi' : reussi})
            else:
                erreur_mail = ""
                erreur_tel = ""
                erreur_cp = ""

                if not Regex.verif_mail(form.cleaned_data['mail']) :
                    erreur_mail = "Mauvais format d'adresse mail"
                if not Regex.verif_tel(form.cleaned_data['telephone']):
                    erreur_tel = "Mauvais format de numéro de téléphone : les chiffres doivent être séparés par des points, des tirets ou des espaces"
                if not Regex.verif_cp(form.cleaned_data['code_postal']):
                    erreur_cp = "Mauvais format de code postal"
                context = {
                    'form' : form,
                    'erreur_mail' : erreur_mail,
                    'erreur_tel' : erreur_tel,
                    'erreur_cp' : erreur_cp
                }
                return render(request, 'inscription/inscription_form.html', context)
        else:
            form = Formulaire_inscription()
        
        return render(request, 'inscription/inscription_form.html', {'form' : form})
    else:
        return HttpResponseRedirect(reverse("inscription:login_secretaire"))

def politique_confidentialite(request):
    return render(request, 'inscription/politique_confidentialite.html')

def Accueil(request):
    return render(request, 'inscription/accueil.html')

def login_secretaire(request):
    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)  # connecter l'utilisateur
                return HttpResponseRedirect(reverse("inscription:accueil_secretaire"))
            else:
                form.add_error(None, 'Le nom d\'utilisateur ou le mot de passe est incorrect.')
    else:
        form = LoginForm()

    return render(request, 'inscription/login_secretaire.html', {'form': form})

def login_nageur(request):
    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)  # connecter l'utilisateur
                request.user.inscription.login_count = request.user.inscription.login_count + 1
                request.user.inscription.save()
                return HttpResponseRedirect(reverse("inscription:accueil_nageur"))
            else:
                form.add_error(None, 'Le nom d\'utilisateur ou le mot de passe est incorrect.')
    else:
        form = LoginForm()

    return render(request, 'inscription/login_nageur.html', {'form': form})

@login_required
def change_password(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            old_password = request.POST.get('old_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            user = authenticate(username=request.user.username, password=old_password)
            if user is not None:
                if new_password1 == new_password2:
                    if old_password != new_password1:  # vérification ajoutée ici
                        if not Regex.verif_mdp(new_password1) :
                            messages.error(request,  "Mauvais format de mot de passe.")
                        else :
                            user.set_password(new_password1)
                            user.save()
                            messages.success(request, 'Votre mot de passe a été modifié avec succès.')
                            if request.user.is_superuser:
                                return HttpResponseRedirect(reverse("inscription:accueil_secretaire"))
                            else:
                                return HttpResponseRedirect(reverse("inscription:accueil_nageur"))
                    else:
                        messages.error(request, 'Le nouveau mot de passe est identique à l\'ancien.')
                else:
                    messages.error(request, 'Les deux nouveaux mots de passe ne correspondent pas.')
            else:
                messages.error(request, 'Le mot de passe actuel est incorrect.')

        return render(request, 'inscription/change_password.html')
    else:
        return HttpResponseRedirect(reverse("inscription:accueil"))

def accueil_secretaire(request):
    if request.user.is_superuser:
        adherents = Inscription.objects.all()
        return render(request, 'inscription/accueil_secretaire.html', {'adherents' : adherents})
    else:
        return HttpResponseRedirect(reverse("inscription:login_secretaire"))
        
@login_required
def nageur(request, adherent_id):
    if request.user.is_superuser:
        nageur = Inscription.objects.get(pk=adherent_id)
        return render(request, 'inscription/nageur.html', {'nageur' : nageur})
    else:
        return HttpResponseRedirect(reverse("inscription:login_secretaire"))

@login_required
def modification_nageur(request, adherent_id):
    if request.user.is_superuser:
        if request.method == 'POST':
            form = Formulaire_inscription(request.POST)
            if form.is_valid() and Regex.verif_mail(form.cleaned_data['mail']) and Regex.verif_tel(form.cleaned_data['telephone']) and Regex.verif_cp(form.cleaned_data['code_postal']):
                reussi = "Utilisateur modifié avec succès"
                adherent = Inscription.objects.get(pk=adherent_id)
                adherent.nom = request.POST['nom']
                adherent.prenom = request.POST['prenom']
                adherent.date_inscription = timezone.now()
                adherent.date_naissance = request.POST['date_naissance']
                adherent.mail = request.POST['mail']
                adherent.telephone = request.POST['telephone']
                adherent.adresse = request.POST['adresse']
                adherent.code_postal = request.POST['code_postal']
                adherent.date_certificat = request.POST['date_certificat']
                adherent.affiche_trombinoscope = request.POST.get('trombinoscope',False)
                adherent.affiche_annuaire = request.POST.get('annuaire',False)
                adherent.cotisation = request.POST.get('cotisation', False)
                adherent.save()
                return render(request, 'inscription/modification_form.html', {'form' : form, 'reussi' : reussi, 'nageur' : adherent})
            else:
                erreur_mail = ""
                erreur_tel = ""
                erreur_cp = ""

                if not Regex.verif_mail(form.cleaned_data['mail']) :
                    erreur_mail = "Mauvais format d'adresse mail"
                if not Regex.verif_tel(form.cleaned_data['telephone']):
                    erreur_tel = "Mauvais format de numéro de téléphone : les chiffres doivent être séparés par des points, des tirets ou des espaces"
                if not Regex.verif_cp(form.cleaned_data['code_postal']):
                    erreur_cp = "Mauvais format de code postal"
                context = {
                    'form' : form,
                    'erreur_mail' : erreur_mail,
                    'erreur_tel' : erreur_tel,
                    'erreur_cp' : erreur_cp
                }
                return render(request, 'inscription/modification_form.html', context)
        else:
            nageur = Inscription.objects.get(pk=adherent_id)
            form = Formulaire_inscription()
        return render(request, 'inscription/modification_form.html', {'nageur' : nageur, 'form' : form})
    else:
        return HttpResponseRedirect(reverse("inscription:login_secretaire"))

@login_required
def archiver_nageur(request, adherent_id):
    if request.user.is_superuser:
        inscription = Inscription.objects.get(pk=adherent_id)
        archive = Archive()
        archive.nom = inscription.nom
        archive.prenom = inscription.prenom
        archive.date_naissance = inscription.date_naissance
        archive.mail = inscription.mail
        archive.telephone = inscription.telephone
        archive.adresse = inscription.adresse
        archive.code_postal = inscription.code_postal
        archive.date_inscription = inscription.date_inscription
        archive.date_desinscription = timezone.now() 
        archive.save()
        
        inscription.delete()
        
        return HttpResponseRedirect(reverse("inscription:accueil_secretaire"))
    else:
        return HttpResponseRedirect(reverse("inscription:login_secretaire"))


def accueil_nageur(request):
    if request.user.is_authenticated and not(request.user.is_superuser):
        nageur = request.user.inscription
        if request.user.inscription.login_count == 1:
            return HttpResponseRedirect(reverse("inscription:change_password"))
        return render(request, 'inscription/accueil_nageur.html', {'nageur' : nageur, 'user' : request.user})
    else:
        return HttpResponseRedirect(reverse("inscription:login_nageur"))

def modification_nageur_nageur(request):
    if request.user.is_authenticated and not(request.user.is_superuser):
        nageur = request.user.inscription
        if request.method == 'POST':
            form = Formulaire_inscription(request.POST)
            if form.is_valid() and Regex.verif_mail(form.cleaned_data['mail']) and Regex.verif_tel(form.cleaned_data['telephone']) and Regex.verif_cp(form.cleaned_data['code_postal']):
                reussi = "Informations modifiées avec succès"
                adherent = Inscription.objects.get(pk=nageur.id)
                adherent.nom = request.POST['nom']
                adherent.prenom = request.POST['prenom']
                adherent.date_inscription = timezone.now()
                adherent.date_naissance = request.POST['date_naissance']
                adherent.mail = request.POST['mail']
                adherent.telephone = request.POST['telephone']
                adherent.adresse = request.POST['adresse']
                adherent.code_postal = request.POST['code_postal']
                adherent.date_certificat = request.POST['date_certificat']
                adherent.affiche_trombinoscope = request.POST.get('trombinoscope',False)
                adherent.affiche_annuaire = request.POST.get('annuaire',False)
                adherent.save()
                return render(request, 'inscription/modification_form.html', {'form' : form, 'reussi' : reussi, 'nageur' : adherent})
            else:
                erreur_mail = ""
                erreur_tel = ""
                erreur_cp = ""

                if not Regex.verif_mail(form.cleaned_data['mail']) :
                    erreur_mail = "Mauvais format d'adresse mail"
                if not Regex.verif_tel(form.cleaned_data['telephone']):
                    erreur_tel = "Mauvais format de numéro de téléphone : les chiffres doivent être séparés par des points, des tirets ou des espaces"
                if not Regex.verif_cp(form.cleaned_data['code_postal']):
                    erreur_cp = "Mauvais format de code postal"
                context = {
                    'form' : form,
                    'erreur_mail' : erreur_mail,
                    'erreur_tel' : erreur_tel,
                    'erreur_cp' : erreur_cp
                }
                return render(request, 'inscription/modification_form.html', context)
        else:
            form = Formulaire_inscription()
        return render(request, 'inscription/modification_form.html', {'nageur' : nageur, 'form' : form})
    else:
        return HttpResponseRedirect(reverse("inscription:login_nageur"))

def logout_view(request):
    logout(request)
    messages.success(request, 'Vous êtes déconnecté.')
    return HttpResponseRedirect(reverse("inscription:Accueil"))


def trombinoscope(request):
    if request.user.is_authenticated and not(request.user.is_superuser):
        adherents = Inscription.objects.all()
        image_list = ['Beatrice.jpeg', 'emma.jpg', 'eva.jpg', 'milan.jpg', 'Tom.jpg', 'Zaboutine.jpg']  # Liste des noms d'images

        context = {
            'adherents': adherents,
            'image_list': image_list,
        }

        return render(request, 'inscription/trombinoscope.html', context)
    else:
        return HttpResponseRedirect(reverse("inscription:login_nageur"))