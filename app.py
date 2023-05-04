# Importing Libraries

import numpy as np

from tkinter import font
import cv2
import os, sys
import time
import operator

from string import ascii_uppercase

import tkinter as tk
from PIL import Image, ImageTk

from hunspell import Hunspell
import enchant

from keras.models import model_from_json

from language_selector import Language
from TextToAudio import TextToAudio
from Translator import TextTranslate


os.environ["THEANO_FLAGS"] = "device=cuda, assert_no_cpu_op=True"

#Application :

class Application:

    def __init__(self):

        self.hs = Hunspell('en_US',"en_CA.dic")
        self.vs = cv2.VideoCapture(0)
        self.current_image = None
        self.current_image2 = None

        languageObject = Language()
        self.pref_lang = languageObject.getSelected()
        self.speech = TextToAudio()
        self.speech.setLang(self.pref_lang)

        self.json_file = open("Models\model_new.json", "r")
        self.model_json = self.json_file.read()
        self.json_file.close()

        self.loaded_model = model_from_json(self.model_json)
        self.loaded_model.load_weights("Models\model_new.h5")

        self.json_file_dru = open("Models\model-bw_dru.json" , "r")
        self.model_json_dru = self.json_file_dru.read()
        self.json_file_dru.close()

        self.loaded_model_dru = model_from_json(self.model_json_dru)
        self.loaded_model_dru.load_weights("Models\model-bw_dru.h5")
        self.json_file_tkdi = open("Models\model-bw_tkdi.json" , "r")
        self.model_json_tkdi = self.json_file_tkdi.read()
        self.json_file_tkdi.close()

        self.loaded_model_tkdi = model_from_json(self.model_json_tkdi)
        self.loaded_model_tkdi.load_weights("Models\model-bw_tkdi.h5")
        self.json_file_smn = open("Models\model-bw_smn.json" , "r")
        self.model_json_smn = self.json_file_smn.read()
        self.json_file_smn.close()

        self.loaded_model_smn = model_from_json(self.model_json_smn)
        self.loaded_model_smn.load_weights("Models\model-bw_smn.h5")

        self.ct = {}
        self.ct['blank'] = 0
        self.blank_flag = 0

        for i in ascii_uppercase:
          self.ct[i] = 0
        
        print("Loaded model from disk")

        self.root = tk.Tk()
        self.root.title("Sign Language To Text Conversion")
        self.root.protocol('WM_DELETE_WINDOW', self.destructor)
        self.root.geometry("1500x900")

        self.panel = tk.Label(self.root)
        self.panel.place(x = 135, y = 10, width = 640, height = 640)
        
        self.panel2 = tk.Label(self.root) # initialize image panel
        self.panel2.place(x = 460, y = 95, width = 310, height = 310)

        self.T = tk.Label(self.root)
        self.T.place(x = 31, y = 17)
        self.T.config(text = "Sign Language To Text Conversion", font = ("Courier", 30, "bold"))

        self.panel3 = tk.Label(self.root) # Current Symbol
        self.panel3.place(x = 1100, y = 95)

        self.T1 = tk.Label(self.root)
        self.T1.place(x = 800, y = 100)
        self.T1.config(text = "Letter :", font = ("Courier", 40, "bold"))

        self.panel4 = tk.Label(self.root) # Word
        self.panel4.place(x = 1150, y = 165)

        self.T2 = tk.Label(self.root)
        self.T2.place(x = 800, y = 170)
        self.T2.config(text = "Word :", font = ("Courier", 40, "bold"))

        self.panel5 = tk.Label(self.root) # Sentence
        self.panel5.place(x = 30,y=750)

        self.T3 = tk.Label(self.root)
        self.T3.place(x = 10, y = 680)
        self.T3.config(text = "Sentence :",font = ("Courier", 20, "bold"))

        # self.T4 = tk.Label(self.root)
        # self.T4.place(x = 250, y = 690)
        # self.T4.config(text = "Suggestions :", fg = "red", font = ("Courier", 30, "bold"))
        
        #Loading message display
        self.loadingMsg = tk.Label(self.root)
        self.loadingMsg.place(x = 10, y = 650)
        self.loadingMsg.config(text='Please Wait While Model is Loading...', font=('Courier', 20))

        self.bt1 = tk.Button(self.root, command = self.action1, height = 0, width = 0)
        self.bt1.place(x = 800, y = 500)

        self.bt2 = tk.Button(self.root, command = self.action2, height = 0, width = 0)
        self.bt2.place(x = 800, y = 450)

        self.bt3 = tk.Button(self.root, command = self.action3, height = 0, width = 0)
        self.bt3.place(x = 800, y = 400)

        self.bt4=tk.Button(self.root, command=self.action4,height = 0,width = 0)
        self.bt4.place(x = 800,y=350)
        
        self.bt5=tk.Button(self.root, command=self.action5,height = 0,width = 0)
        self.bt5.place(x = 800,y=300)
        
        #NextButton
        self.btcall_next = tk.Button(self.root,command = self.nextWord,height = 0,width = 0)
        self.btcall_next.config(text = "Next",font = ("Courier",14))
        self.btcall_next.place(x = 950, y = 450)

        #ClearButton
        self.btcall_clear = tk.Button(self.root,command = self.clearWord,height = 0,width = 0)
        self.btcall_clear.config(text = "Clear",font = ("Courier",14))
        self.btcall_clear.place(x = 1100, y = 450)

        #TranslateButton
        self.btcall_translate = tk.Button(self.root,command = self.showResult,height = 0,width = 0)
        self.btcall_translate.config(text = "Translated Audio",font = ("Courier",14))
        self.btcall_translate.place(x = 1250, y = 450)

        self.str = ""
        self.word = " "
        self.current_symbol = "Empty"
        self.photo = "Empty"
        self.video_loop()


    def video_loop(self):
        ok, frame = self.vs.read()

        if ok:
            cv2image = cv2.flip(frame, 1)

            x1 = int(0.5 * frame.shape[1])
            y1 = 10
            x2 = frame.shape[1] - 10
            y2 = int(0.5 * frame.shape[1])

            cv2.rectangle(frame, (x1 - 1, y1 - 1), (x2 + 1, y2 + 1), (255, 0, 0) ,1)
            cv2image = cv2.cvtColor(cv2image, cv2.COLOR_BGR2RGBA)

            self.current_image = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image = self.current_image)

            self.panel.imgtk = imgtk
            self.panel.config(image = imgtk)

            cv2image = cv2image[y1 : y2, x1 : x2]

            gray = cv2.cvtColor(cv2image, cv2.COLOR_BGR2GRAY)

            blur = cv2.GaussianBlur(gray, (5, 5), 2)

            th3 = cv2.adaptiveThreshold(blur, 255 ,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

            ret, res = cv2.threshold(th3, 70, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            self.predict(res)

            self.current_image2 = Image.fromarray(res)

            imgtk = ImageTk.PhotoImage(image = self.current_image2)

            self.panel2.imgtk = imgtk

            self.panel2.config(image = imgtk)
            self.panel3.config(text = self.current_symbol, font = ("Courier", 40, 'bold'))
            self.panel4.config(text = self.word, font = ("Courier", 30))
            self.panel5.config(text = self.str,font = ("Courier", 20))

            predicts = self.hs.suggest(self.word)
            
            if(len(predicts) > 0):
                self.bt1.config(text=predicts[0],font = ("Courier",20))
            else:
                self.bt1.config(text="")

            if(len(predicts) > 1):
                self.bt2.config(text=predicts[1],font = ("Courier",20))
            else:
                self.bt2.config(text="")

            if(len(predicts) > 2):
                self.bt3.config(text=predicts[2],font = ("Courier",20))
            else:
                self.bt3.config(text="")

            if(len(predicts) > 3):
                self.bt4.config(text=predicts[3],font = ("Courier",20))
            else:
                self.bt4.config(text="")

            if(len(predicts) > 4):
                self.bt5.config(text=predicts[4],font = ("Courier",20))
            else:
                self.bt5.config(text="")     

        self.root.after(30, self.video_loop)

    def predict(self, test_image):

        test_image = cv2.resize(test_image, (128, 128))

        result = self.loaded_model.predict(test_image.reshape(1, 128, 128, 1))


        result_dru = self.loaded_model_dru.predict(test_image.reshape(1 , 128 , 128 , 1))

        result_tkdi = self.loaded_model_tkdi.predict(test_image.reshape(1 , 128 , 128 , 1))

        result_smn = self.loaded_model_smn.predict(test_image.reshape(1 , 128 , 128 , 1))

        prediction = {}

        prediction['blank'] = result[0][0]

        inde = 1

        for i in ascii_uppercase:

            prediction[i] = result[0][inde]

            inde += 1

        #LAYER 1

        prediction = sorted(prediction.items(), key = operator.itemgetter(1), reverse = True)

        self.current_symbol = prediction[0][0]


        #LAYER 2

        if(self.current_symbol == 'D' or self.current_symbol == 'R' or self.current_symbol == 'U'):
            prediction = {}

            prediction['D'] = result_dru[0][0]
            prediction['R'] = result_dru[0][1]
            prediction['U'] = result_dru[0][2]

            prediction = sorted(prediction.items(), key = operator.itemgetter(1), reverse = True)

            self.current_symbol = prediction[0][0]

        if(self.current_symbol == 'D' or self.current_symbol == 'I' or self.current_symbol == 'K' or self.current_symbol == 'T'):

            prediction = {}
            prediction['D'] = result_tkdi[0][0]
            prediction['I'] = result_tkdi[0][1]
            prediction['K'] = result_tkdi[0][2]
            prediction['T'] = result_tkdi[0][3]

            prediction = sorted(prediction.items(), key = operator.itemgetter(1), reverse = True)

            self.current_symbol = prediction[0][0]

        if(self.current_symbol == 'M' or self.current_symbol == 'N' or self.current_symbol == 'S'):

            prediction1 = {}

            prediction1['M'] = result_smn[0][0]
            prediction1['N'] = result_smn[0][1]
            prediction1['S'] = result_smn[0][2]

            prediction1 = sorted(prediction1.items(), key = operator.itemgetter(1), reverse = True)

            if(prediction1[0][0] == 'S'):

                self.current_symbol = prediction1[0][0]

            else:

                self.current_symbol = prediction[0][0]
        
        if(self.current_symbol == 'blank'):

            for i in ascii_uppercase:
                self.ct[i] = 0

        self.ct[self.current_symbol] += 1

        if(self.ct[self.current_symbol] > 60):

            for i in ascii_uppercase:
                if i == self.current_symbol:
                    continue

                tmp = self.ct[self.current_symbol] - self.ct[i]

                if tmp < 0:
                    tmp *= -1

                if tmp <= 20:
                    self.ct['blank'] = 0

                    for i in ascii_uppercase:
                        self.ct[i] = 0
                    return

            self.ct['blank'] = 0

            for i in ascii_uppercase:
                self.ct[i] = 0

            if self.current_symbol == 'blank':

                if self.blank_flag == 0:
                    self.blank_flag = 1

                    if len(self.str) > 0:
                        self.str += " "

                    self.str += self.word

                    self.word = ""

            else:

                if(len(self.str) > 16):
                    self.str = ""

                self.blank_flag = 0

                self.word += self.current_symbol

    def action1(self):

        predicts = self.hs.suggest(self.word)

        if(len(predicts) > 0):

            self.word = ""

            self.str += " "

            self.str += predicts[0]

    def action2(self):

        predicts = self.hs.suggest(self.word)

        if(len(predicts) > 1):
            self.word = ""
            self.str += " "
            self.str += predicts[1]

    def action3(self):

        predicts = self.hs.suggest(self.word)

        if(len(predicts) > 2):
            self.word = ""
            self.str += " "
            self.str += predicts[2]

    def action4(self):

        predicts = self.hs.suggest(self.word)
        
        if(len(predicts) > 3):
            self.word = ""
            self.str += " "
            self.str += predicts[3]

    def action5(self):
        
        predicts = self.hs.suggest(self.word)

        if(len(predicts) > 4):
            self.word = ""
            self.str += " "
            self.str += predicts[4]
            
    def destructor(self):

        print("Closing Application...")

        self.root.destroy()
        self.vs.release()
        del self.speech
        cv2.destroyAllWindows()

    def nextWord(self):
        self.str+=" "
        self.str+=self.word
        self.word=""

    def clearWord(self):
        self.word=""
        
    def showResult(self):
        #Translating Text
        self.translate = TextTranslate()
        self.translate.initialize(lang_ab=self.pref_lang, text=self.str)
        self.translatedText = self.translate.translateText()
        
        #Converting to Audio
        self.speech.setText(self.translatedText)
        self.speech.toSpeech() #Audio file Generate
        self.speech.playAudio() #Play Audio
        del self.speech
        self.speech = TextToAudio()
        self.speech.setLang(self.pref_lang)
    
print("Starting Application...")

(Application()).root.mainloop()