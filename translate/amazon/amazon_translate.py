import boto3
import io
from io import BytesIO
import math
from PIL import Image, ImageDraw, ImageFont
import xmltodict
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import time
from time import sleep
import botocore
from awsretry import AWSRetry
import logging
import sys
import os
# [TODO]: Implement the logging once the basic implementation is done.
# Fix the initial tags 
# implement changing the exponential weight decay
class Atranslate(object):
 	"""docstring for translate"""

 	def __init__(self, src_dir, dst_dir, src_lang, dst_lang, terminology=None):
 		super(Atranslate, self).__init__()
 		self.src_dir = src_dir
 		self.dst_dir = dst_dir
 		self.src_lang = src_lang
 		self.dst_lang = dst_lang
 		self.terminology = terminology
 		self.translate = boto3.client('translate')
 		self.codes = ['zh-TW']
 		logging.basicConfig(filename='logs/hol-2003-01-net_xml_en.log',
                    filemode='a', format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', level=logging.INFO, datefmt='%H:%M:%S')
 		self.logger = logging.getLogger('Translation')
 		if dst_lang not in self.codes:
 			self.logger.info("The provided language code is out of the hol supported lab catalog codes!!")
 			self.logger.error(
 			    "The provided language code is out of the hol supported lab catalog codes!!")

 	def awsAuthenticate(self):
 		pass

 	def connectBoto(self):
 		pass

 	@AWSRetry.backoff(tries=20, delay=2, backoff=1.5, added_exceptions=['ConcurrentTagAccess', 'ThrottlingException'])
 	def language_translation(self, text, source_language, target_language):
 		# print("transafjsflsjgl", text) 
 		try:
 			translated_text = self.translate.translate_text(
 			    Text=text, SourceLanguageCode=source_language, TargetLanguageCode=target_language)
 		except botocore.exceptions.ClientError as e:
 			raise e
 		return translated_text

 	def findOccurrences(self, s, ch):
 		return [i for i, letter in enumerate(s) if letter == ch]


 	def longText(self, text_translate, target_language_code):
 		res = ""
 		self.logger.info("Current frame size exceed limits, breaking down the frame")
 		soup = BeautifulSoup(text_translate, 'html.parser')
 		for soup_text in soup.children:
 			soup_text = str(soup_text)
 			soup_len = len(soup_text)
 			# self.logger.info("length of soup text", len(str(soup_text)))
 			if soup_len<5000:
 				result = self.language_translation( text= str(soup_text), source_language="en", target_language=target_language_code)
 				res += str(result.get('TranslatedText'))
 				self.logger.info(result.get('TranslatedText'))
 			else:
 				self.logger.info("Needs to break down the text further to process")
 				list_occ = self.findOccurrences(soup_text, '>')
 				split_index = len(list_occ)//2
 				first_half = soup_text[:split_index+1]
 				second_half = soup_text[split_index+1:]
 				first_trans = self.language_translation( text= first_half, source_language="en", target_language=target_language_code)
 				res += str(first_trans.get('TranslatedText'))
 				second_trans = self.language_translation( text= second_half, source_language="en", target_language=target_language_code)
 				res += str(first_trans.get('TranslatedText'))
 		return res



 	def main(self):
 		start_time = time.time()
 		translate = boto3.client('translate')
 		source_language = "en"
 		total_char = 0
 		print("Translating lab manual hol-2003-01-net_xml_en")
 		for target_language_code in self.codes:
 			print("Translating content from {}  to {}".format(
 			    source_language, target_language_code))
 			with open(self.src_dir + '/hol-2003-01-net_xml_en/content.xml') as f:
 				tree = ET.parse(f)
 				root = tree.getroot()
 				len_of_text = 0
 			for elem in root.getiterator():
 				text_translate = elem.text
 				if text_translate is None or text_translate.isspace():
 					continue
 				else:
 					self.logger.info(
 					    "---------------------Start of text----------------------------------")
 					self.logger.info(
 					    "-----------------------translating text-----------------------------")
 					curr_len = len(text_translate.encode('utf-8'))
 					total_char += curr_len
 					# self.logger.info("current frame size", str(curr_len))
 					if curr_len > 5000:
 						elem.text =  self.longText(text_translate, target_language_code)
 					else:
 						result = self.language_translation( text=
						    text_translate,  source_language="en", target_language=target_language_code)
 						self.logger.info(result.get('TranslatedText'))
 						elem.text = str(result.get('TranslatedText'))
 					len_of_text += curr_len
 					# self.logger.info("Length so far.....", len_of_text)
 					self.logger.info("-----------------------translation complete-----------------------------")
 					self.logger.info("---------------------End of text----------------------------------")
 					self.logger.info("")   
 			os.mkdir(self.dst_dir + '/hol-2003-01-net_xml_' + target_language_code)
 			tree.write(self.dst_dir + '/hol-2003-01-net_xml_'+target_language_code+'/content.xml', encoding= "UTF-8")
 			end_time = time.time()
 			print("Total elapsed time to translate the xml document in minute is", (end_time-start_time)/60)
 		final_end_time = time.time()
 		print("Total characters processed in this translation are {} chars".format(total_char))
 		print("Total Translation time {} hour".format((final_end_time-start_time)/3600))

if __name__ == "__main__":
	defaults = {
	'src_dir':"source",
	'dst_dir':"target",
	'src_lang':"en",
	'dst_lang':"es"
	}
	print("Running the translate application")
	trans  = Atranslate(src_dir = defaults['src_dir'], dst_dir = defaults['dst_dir'], src_lang=defaults['src_lang'], dst_lang = defaults['dst_lang'])
	trans.main()

 		
