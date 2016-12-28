#!/usr/bin/python
#--------------------------------------
#    ___  ___  _ ____
#   / _ \/ _ \(_) __/__  __ __
#  / , _/ ___/ /\ \/ _ \/ // /
# /_/|_/_/  /_/___/ .__/\_, /
#                /_/   /___/
#
#  lcd_16x2.py
#  16x2 LCD Test Script
#
# Author : Matt Hawkins
# Date   : 06/04/2015
#
# http://www.raspberrypi-spy.co.uk/
#
#--------------------------------------
 
# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND
 
#import
import RPi.GPIO as GPIO
import time

class hd44780:


	LCD_RS = 7
	LCD_E  = 8
	LCD_D4 = 18
	LCD_D5 = 23
	LCD_D6 = 24
	LCD_D7 = 25

	# Define some device constants
	LCD_WIDTH = 16    # Maximum characters per line
	LCD_CHR = True
	LCD_CMD = False
 
	LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
	LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
 
	# Timing constants
	E_PULSE = 0.0005
	E_DELAY = 0.0005
 
	# Constructor
	def __init__(self):
 
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
		GPIO.setup(self.LCD_E, GPIO.OUT)  # E
		GPIO.setup(self.LCD_RS, GPIO.OUT) # RS
		GPIO.setup(self.LCD_D4, GPIO.OUT) # DB4
		GPIO.setup(self.LCD_D5, GPIO.OUT) # DB5
		GPIO.setup(self.LCD_D6, GPIO.OUT) # DB6
		GPIO.setup(self.LCD_D7, GPIO.OUT) # DB7
		
		# Initialise display
		self.lcd_byte(0x33,self.LCD_CMD) # 110011 Initialise
		self.lcd_byte(0x32,self.LCD_CMD) # 110010 Initialise
		self.lcd_byte(0x06,self.LCD_CMD) # 000110 Cursor move direction
		self.lcd_byte(0x0C,self.LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
		self.lcd_byte(0x28,self.LCD_CMD) # 101000 Data length, number of lines, font size
		self.lcd_byte(0x01,self.LCD_CMD) # 000001 Clear display
		time.sleep(self.E_DELAY)
 
 	def customChar(self, charCode, data):
	 	self.lcd_byte(0x40 + charCode*8, self.LCD_CMD)
 		for i in data:
			self.lcd_byte(i,self.LCD_CHR)
 
 
	def lcd_byte(self, bits, mode):
		# Send byte to data pins
		# bits = data
		# mode = True  for character
		#        False for command
 
 		GPIO.output(self.LCD_RS, mode) # RS
 
		# High bits
		GPIO.output(self.LCD_D4, False)
		GPIO.output(self.LCD_D5, False)
		GPIO.output(self.LCD_D6, False)
		GPIO.output(self.LCD_D7, False)
		if bits&0x10==0x10:
			GPIO.output(self.LCD_D4, True)
		if bits&0x20==0x20:
			GPIO.output(self.LCD_D5, True)
		if bits&0x40==0x40:
			GPIO.output(self.LCD_D6, True)
		if bits&0x80==0x80:
			GPIO.output(self.LCD_D7, True)
 
		# Toggle 'Enable' pin
		self.lcd_toggle_enable()
 
		# Low bits
		GPIO.output(self.LCD_D4, False)
		GPIO.output(self.LCD_D5, False)
		GPIO.output(self.LCD_D6, False)
		GPIO.output(self.LCD_D7, False)
		if bits&0x01==0x01:
			GPIO.output(self.LCD_D4, True)
		if bits&0x02==0x02:
			GPIO.output(self.LCD_D5, True)
		if bits&0x04==0x04:
			GPIO.output(self.LCD_D6, True)
		if bits&0x08==0x08:
			GPIO.output(self.LCD_D7, True)
 
		# Toggle 'Enable' pin
		self.lcd_toggle_enable()
 
 
	def lcd_toggle_enable(self):
		# Toggle enable
		time.sleep(self.E_DELAY)
		GPIO.output(self.LCD_E, True)
		time.sleep(self.E_PULSE)
		GPIO.output(self.LCD_E, False)
		time.sleep(self.E_DELAY)
 
 	def line1(self,message):
 		self.lcd_string(message,self.LCD_LINE_1)
 		
 	def line2(self,message):
 		self.lcd_string(message,self.LCD_LINE_2)
 
	def lcd_string(self, message,line):
		# Send string to display
		message = message.ljust(self.LCD_WIDTH," ")
		self.lcd_byte(line, self.LCD_CMD)

		for i in range(self.LCD_WIDTH):
			self.lcd_byte(ord(message[i]),self.LCD_CHR)
 
	def cleanup(self):
		self.lcd_byte(0x01, self.LCD_CMD)
		GPIO.cleanup()
