from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib.auth.hashers import check_password, make_password
from SewakarApp.models import SignUp
from SewakarApp.models.EmailConfirmation import Confirmation
from django.views import View
import socket

from smtplib import SMTP
import datetime


class Login(View):
    return_url = None
    service = None

    def get(self, request):
        Login.return_url = request.GET.get('return_url')
        Login.service = request.GET.get('service')
        print(Login.service)

        session_id = request.session.get('id')
        if session_id:
            return redirect('profile')
        else:
            if request.GET.get('return_url'):
                Login.return_url = request.GET.get('return_url')
            return render(request, "login.html")

    def post(self, request):
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        People = SignUp.get_people_by_email(email)

        error_massage = None
        if People:
            flag = check_password(password, People.Password)
            if flag:
                if People.status:
                    request.session['id'] = People.id
                    request.session['first_name'] = People.First_name
                    request.session['last_name'] = People.Last_name
                    request.session['category'] = People.Category.id
                    if People.Category.id == 3:
                        request.session['Admin'] = People.Category.id
                    if People.Category.id == 2:
                        request.session['Worker'] = People.Category.id
                    if Login.return_url:
                        if Login.service:
                            return HttpResponseRedirect(f'{Login.return_url}&service={Login.service}')
                        return HttpResponseRedirect(Login.return_url)
                    else:
                        Login.return_url = None
                        Login.sector = None
                        Login.service = None
                        return redirect('main')
                else:
                    request.session['email'] = People.Email
                    return redirect('Activate_Account')
            else:
                error_massage = 'Entered Password is invalid !!'
        else:
            error_massage = 'Email or Password invalid !!'

        return render(request, "login.html", {'error': error_massage, 'email': email})


def logout(request):
    request.session.clear()
    return redirect('login')


def Activate_Account(request):
    msg = request.GET.get('Confirm_msg')
    Get_Code = request.GET.get('Activated_Link')
    Email_on_login = request.POST.get('Email')
    if Get_Code:
        User = Confirmation.objects.get(Code=Get_Code).User
        User.status = True
        User.save()
        Confirmation.objects.get(Code=Get_Code).delete()
        return redirect('login')

    if Email_on_login:
        code_valide = make_password(Email_on_login)
        user = SignUp.objects.get(Email=Email_on_login)

        #host = socket.gethostname()
        #debuglevel = 0
        #smtp = SMTP()
        #smtp.set_debuglevel(debuglevel)
        #smtp.connect('smtp.hostinger.com', 587)
        #smtp.helo(host)
        #smtp.login('ak@sewakar.com', 'Aryan@1234')
        #code, message = smtp.rcpt(str(Email_on_login))

        debuglevel = 0
        smtp = SMTP()
        smtp.set_debuglevel(debuglevel)
        smtp.connect('smtp.hostinger.com', 587)

        if not Confirmation.Get_Code_By_User(user):
            confirm = Confirmation(User=user,
                                   Code=code_valide)
            confirm.register()

        smtp.login('ak@sewakar.com', 'Aryan@1234')
        from_addr = 'Sewakar<support@sewakar.com>'
        to_addr = request.session['email']
        sub = 'Email verification link'
        date = datetime.datetime.now()

        verification_code = Confirmation.objects.get(user)
        mail_text = f"Your verification Link is http://www.sewakar.com/Activate_Account?" \
                    f"Activated_Link={verification_code}"

        msg = f'From:{from_addr}\nTo:{to_addr}\nSubject:{sub}\nDate:{date}\nMassage:{mail_text}'
        smtp.sendmail(from_addr, to_addr, msg)
        smtp.quit()
        request.session.clear()

        return redirect(
            f'Activate_Account?Confirm_msg=Your Confirmation massage will be send in 24 h on your registered '
            f'Email at '
            f'{Email_on_login}'
        )
        smtp.quit()

    return render(request, 'activate_account.html', {'msg': msg})


def Send_Activation_Email(request):
    debuglevel = 0
    smtp = SMTP()
    smtp.set_debuglevel(debuglevel)
    smtp.connect('smtp.hostinger.com', 587)
    smtp.login('ak@sewakar.com', 'Aryan@1234')
    from_addr = 'Sewakar<support@sewakar.com>'
    to_addr = request.session['email']
    sub = 'Email verification link'
    date = datetime.datetime.now()

    user = SignUp.objects.get(Email=to_addr)
    verification_code = Confirmation.objects.get(user)
    mail_text = f"Your verification Link is http://www.sewakar.com/Activate_Account?Activated_Link={verification_code}"

    msg = f'From:{from_addr}\nTo:{to_addr}\nSubject:{sub}\nDate:{date}\nMassage:{mail_text}'
    smtp.sendmail(from_addr, to_addr, msg)
    smtp.quit()

    request.session.clear()
    return redirect('login')
