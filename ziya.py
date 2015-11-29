#!/usr/bin/python


import Tkinter as tk
import speech_recognition as sr
import threading
import pyttsx
import wolframalpha


class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        master.title("Ziya")
        master.geometry("300x120+600+300")
        master.resizable(width=False, height=False)

        self.stt_engine = sr.Recognizer()
        self.wolfram = wolframalpha.Client('4WV7UK-EXPG3V2UK6')

        self.pack()
        self.createWidgets()

    def createWidgets(self):
        self.input_label = tk.Label(self, text='Welcome to Ziya')
        self.input_label.pack(pady=5)

        self.results_label = tk.Label(self,)
        self.results_label.pack(pady=5)

        self.process_voice_btn = tk.Button(self)
        self.process_voice_btn["text"] = "Run Ziya"
        self.process_voice_btn["command"] = self.process_voice
        self.process_voice_btn.pack(side='top', pady=5)

    def process_voice(self):
        self.process_voice_btn['state'] = 'disabled'

        def background_thread():
            with sr.Microphone() as source:
                self.input_label["text"] = "Say something!"
                audio = self.stt_engine.listen(source)

            try:
                # for testing purposes, we're just using the default API key
                # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
                # instead of `r.recognize_google(audio)`
                user_input = self.stt_engine.recognize_google(audio)
                self.input_label["text"] = 'Input: ' + user_input
                results = list(self.wolfram.query(user_input).results)

                if results:
                    self.results_label["text"] = 'Results: ' + results[0].text
                    engine = pyttsx.init()
                    engine.say(results[0].text)
                    engine.runAndWait()
                else:
                    self.results_label["text"] = 'No results'
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))

            self.process_voice_btn['state'] = 'normal'

        t = threading.Thread(target=background_thread)
        t.start()

root = tk.Tk()
app = Application(master=root)
app.mainloop()
