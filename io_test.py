import os
import threading
import time

import pygame

import gaugette.rotary_encoder
import gaugette.switch

import pyttsx
import speech_recognition as sr
from most.voip.api import VoipLib
import random

import schiene

bahn = schiene.Schiene()

stt_engine = sr.Recognizer()

voip_caller = None
stop_call = False


def make_call(number):
    global voip_caller
    if voip_caller is None:
        voip_caller = VoipLib()
        voip_params = {u'username': u'ziyapi',  # a name describing the user
                       u'sip_server_address': u'sip.linphone.org',  # the ip of the remote sip server (default port: 5060)
                       u'sip_server_user': u'ziyapi',  # the username of the sip account
                       u'sip_server_pwd': u'******',  # the password of the sip account
                       u'sip_server_transport': u'udp',  # the transport type (default: tcp)
                       u'log_level': 1,  # the log level (greater values provide more informations)
                       u'debug': True  # enable/disable debugging messages
                       }

        def notify_events(voip_event_type, voip_event, params):
            print "Received Event Type:%s -> Event: %s Params: %s" % (voip_event_type, voip_event, params)

        voip_caller.init_lib(voip_params, notify_events)
        voip_caller.register_account()

    voip_caller.make_call(number)

    while True:
        global wheel_last_state
        sw_state = wheel_switch.get_state()
        if sw_state != wheel_last_state:
            wheel_last_state = sw_state
            voip_caller.hangup_call()
            global state
            state = 'waiting'
            print_lcd_text(['Welcome', 'to', 'Ziya'])
            break


def tts_say(text):
    def background_thread():
        tts_engine = pyttsx.init()
        tts_engine.say(text)
        tts_engine.runAndWait()
    t = threading.Thread(target=background_thread)
    t.start()

stt_result = ''


def process_voice():
    import pyaudio
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        print p.get_device_info_by_index(i)

    def background_thread():
        global stt_result
        with sr.Microphone(device_index=5) as source:
            print("Say something!")
            audio = stt_engine.listen(source)

        try:
            user_input = stt_engine.recognize_google(audio)
            stt_result = user_input
            return

        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

        stt_result = ''

    t = threading.Thread(target=background_thread)
    t.start()
    t.join()
    return stt_result

system_volume = None


def set_volume(volume):
    os.system('amixer set Speaker {}%'.format(volume))
    system_volume = volume

set_volume(80)

os.putenv('SDL_FBDEV', '/dev/fb1')
pygame.font.init()
lcd = pygame.display.set_mode((480, 320), pygame.FULLSCREEN)

lcd.fill((0, 0, 255))
pygame.display.update()

lcd_text = []
text_center_x = None
text_center_y = None


def print_lcd_text(text, center_x=None, center_y=None):
    global text_center_x
    global text_center_y
    global lcd_text
    lcd_text = text
    if center_x:
        text_center_x = center_x
    else:
        text_center_x = 240

    if center_y:
        text_center_y = center_y
    else:
        text_center_y = 280


    tmp_y_center = text_center_y
    lcd.fill((0, 0, 255))
    font_big = pygame.font.SysFont("ttf-dejavu", 100)
    formated_text = [line[i:i+12] for line in text for i in range(0, len(line), 12)]
    for line in formated_text:
        text_surface = font_big.render('%s' % line, True, (255, 255, 255))
        text_surface = pygame.transform.rotate(text_surface, 180)
        rect = text_surface.get_rect(center=(text_center_x, tmp_y_center))
        tmp_y_center -= 70
        lcd.blit(text_surface, rect)
    pygame.display.update()


# WHEEL_GND_PIN blue
WHEEL_A_PIN = 7  # white
WHEEL_B_PIN = 9  # yellow
WHEEL_SW_PIN = 8
FRONT_SW_PIN = 15

encoder = gaugette.rotary_encoder.RotaryEncoder(WHEEL_A_PIN, WHEEL_B_PIN)
encoder.steps_per_cycle = 2

wheel_switch = gaugette.switch.Switch(WHEEL_SW_PIN)
front_switch = gaugette.switch.Switch(FRONT_SW_PIN)

wheel_last_state = None
front_last_state = None
state = 'waiting'
print_lcd_text(['Welcome', 'to', 'Ziya'])
while True:
    cycle = encoder.get_cycles()
    if cycle !=0:
        print "rotate %d" % cycle
        if state != 'waiting':
            print_lcd_text(lcd_text, center_y=text_center_y + cycle*10)

    sw_state = wheel_switch.get_state()
    if sw_state != wheel_last_state:
        print "wheel switch %d" % sw_state
        state = 'waiting'
        print_lcd_text(['Welcome', 'to', 'Ziya'])
        wheel_last_state = sw_state

    sw_state = front_switch.get_state()
    if sw_state != front_last_state:
        print "front switch %d" % sw_state
        if sw_state == 1 and state == 'waiting':
            state = 'voice'
            print_lcd_text(['Please', 'speak'])
            request = process_voice()
            if 'call contact' in request and len(request.split(' ')) == 3:
                state = 'call'
                contacts = {'one': 'evil_crab'}
                number = contacts.get(request.split(' ')[-1])
                if number is not None:
                    print_lcd_text(['Calling', number])
                    make_call(number)
                else:
                    print_lcd_text(['Contact', request.split(' ')[-1], 'not', 'found'])
                    time.sleep(3)
                    state = 'waiting'
                    print_lcd_text(['Welcome', 'to', 'Ziya'])
            elif 'find train from' in request and len(request.split(' ')) == 6:
                state = 'train'
                txt = ['Train', 'from', request.split(' ')[-3], 'to', request.split(' ')[-1], 'departs in', '{} minutes'.format(random.randint(5, 60))]
                print_lcd_text(txt)
                time.sleep(1)
                tts_say(' '.join(txt))
            else:
                state = 'waiting'
                print_lcd_text(['Welcome', 'to', 'Ziya'])

        front_last_state = sw_state
