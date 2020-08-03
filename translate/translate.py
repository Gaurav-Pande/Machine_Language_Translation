from google.cloud import translate_v2 as translatev2
from google.cloud import translate
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
import six
import os
import argparse
import re
import boto3
import botocore
import zipfile
from zipfile import ZipFile
from distutils.dir_util import copy_tree
import shutil
from amazon.amazon_translate import Atranslate

class Translate(object):
 	"""docstring for translate"""
 	def __init__(self, bucket_name, src_dir, dst_dir, model, terminology=None):
 		super(Translate, self).__init__()
 		self.bucket_name = bucket_name
 		self.src_dir = src_dir
 		self.dst_dir = dst_dir
 		self.modelType = model
 		self.terminology = terminology
 		self.translate = translatev2.Client()
 		# self.codes = ['es']
 		self.codes = ['de','es','fr','it','ja','ko','pt','ru','zh','zh-TW']
 		# self.codes = ['zh','zh-TW']
 		self.client = translate.TranslationServiceClient()
 		self.project_id = '473378358434'
 		# text = 'YOUR_SOURCE_CONTENT'
 		self.location = 'us-central1'
 		self.model = 'projects/473378358434/locations/us-central1/models/TRL8487211618663399424'
 		self.parent = self.client.location_path(self.project_id, self.location)
 		self.download_s3(self.src_dir, self.bucket_name)
 		logging.basicConfig(filename='logs/all_logs.log',
                    filemode='a', format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', level=logging.INFO, datefmt='%H:%M:%S')
 		self.logger = logging.getLogger('Translation')

 	def upload_file(self, file_name, bucket, object_name=None):
 		if object_name is None:
 			object_name = file_name
 		s3_client = boto3.client('s3')
 		try:
 			response = s3_client.upload_file(file_name, bucket, object_name)
 		except ClientError as e:
 			logging.error(e)
 			return False
 		return True

 	def upload_s3(self, filename, dst_dir, bucket_name, lab_name, file_language_name):
 		print("Uploading the converted documents to s3 bucket {}".format(bucket_name))
 		# print(self.dst_dir+'/'+file_language_name)
 		shutil.make_archive(self.dst_dir+'/'+file_language_name, 'zip', self.dst_dir+'/'+file_language_name)
 		# os.remove(self.dst_dir+'/'+file_language_name)
 		# print("aws s3 cp " + src_dir + " s3://"+ bucket_name + "/"+ dst_dir +"/"+ lab_name  + " --quiet --recursive")
 		# command = "aws s3 cp " + src_dir + " s3://"+ bucket_name + "/"+ dst_dir +"/"+ lab_name + "/" + file_language_name + ".zip" + " --quiet --recursive"
 		return self.upload_file(filename, bucket_name)


 	def download_s3(self, src_dir, bucket_name):
 		# fetch all the keys
 		keys = []
 		s3 = boto3.client("s3")
 		res = boto3.resource('s3')
 		all_objects = s3.list_objects(Bucket = bucket_name) 
 		# all_objects['Contents']
 		for k in all_objects['Contents']:
 			if re.search('^source/hol', k['Key']):
 				file_name = k['Key'].split('/')[-1]
 				keys.append((k['Key'],file_name))
 		for key in keys:
 			KEY, FILE_NAME = key
 			try:
 				res.Bucket(bucket_name).download_file(KEY, FILE_NAME)
 				with zipfile.ZipFile(FILE_NAME, 'r') as zip_ref:
 					zip_ref.extractall(src_dir) 
 				os.remove(FILE_NAME)
 			except botocore.exceptions.ClientError as e:
 				if e.response['Error']['Code'] == "404":
 					print("The object does not exist.")
 				else:
 					raise


 	def language_translation(self, text, source_language, target_language, model):
 		# print("transafjsflsjgl", text) 
 		if isinstance(text, six.binary_type):
 			text = text.decode('utf-8')
 		if model == 'default':
	 		try:
	 			translated_text = self.translate.translate(
	 			    text, target_language=target_language)
	 		except botocore.exceptions.ClientError as e:
	 			raise e
	 		return translated_text
	 	else:
	 		response = self.client.translate_text(
	 			parent=self.parent,
	 			contents=[text],
	 			model=self.model,
	 			mime_type='text/html',  # mime types: text/plain, text/html
	 			source_language_code='en',
	 			target_language_code='es')
	 		for translation in response.translations:	
	 			return translation.translated_text

 	def main(self):
 		begin = time.time()
 		# translate = boto3.client('translate')
 		source_language = "en"
 		total_char = 0
 		labs = [ f.path for f in os.scandir(self.src_dir) if f.is_dir()]
 		for lab in labs:
 			print("Translating lab manual: {}".format(lab))
 			start_time = time.time()
	 		for target_language_code in self.codes:
	 			start_time_lab = time.time()
	 			print("##########################################################")
	 			print("Translating content from {}  to {}".format(
	 			    source_language, target_language_code))
	 			with open(str(lab) + '/content.xml') as f:
	 				tree = ET.parse(f)
	 				root = tree.getroot()
	 				len_of_text = 0
	 			for elem in root.getiterator():
	 				text_translate = elem.text
	 				tag = elem.tag
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
	 					if tag == 'name' or tag== 'dataFormat':
	 						continue
	 					if tag == 'defaultLanguageCode':
	 						elem.text = str(target_language_code)
	 						continue
	 					result = self.language_translation( text=
							    text_translate,  source_language="en", target_language=target_language_code, model= self.modelType)
	 					# print(result['translatedText'])
	 					if self.modelType == 'custom':
	 						self.logger.info(result)
	 						elem.text = str(result)
	 					else:
	 						self.logger.info(result['translatedText'])
	 						elem.text = str(result['translatedText'])
	 					len_of_text += curr_len
	 					# self.logger.info("Length so far.....", len_of_text)
	 					self.logger.info("-----------------------translation complete-----------------------------")
	 					self.logger.info("---------------------End of text----------------------------------")
	 					self.logger.info("")   
	 			# os.mkdir(self.dst_dir + '/' + str(lab[7:-2]) + target_language_code)
	 			if not os.path.isdir(self.dst_dir + '/' + str(lab[7:-2]) + target_language_code):
	 				os.mkdir(self.dst_dir + '/' + str(lab[7:-2]) + target_language_code)
	 				os.mkdir(self.dst_dir + '/' + str(lab[7:-2]) + target_language_code + '/images')
	 			tree.write(self.dst_dir + '/'+str(lab[7:-2]) + target_language_code+'/content.xml', encoding= "UTF-8")
	 			copy_tree(str(lab)+ '/images', self.dst_dir + '/' + str(lab[7:-2]) + target_language_code + '/images')
	 			end_time = time.time()
	 			print("Total elapsed time to translate the xml document is: {} minutes".format((end_time-start_time_lab)/60))
	 			is_upload = self.upload_s3(self.dst_dir + '/' + str(lab[7:-2]) + target_language_code + '.zip', self.dst_dir , self.bucket_name, str(lab[7:-2])+"all_translations", str(lab[7:-2]) + target_language_code)
	 			if not is_upload:
	 				print("Upload failed....Exiting!!")
	 				exit(0)
	 		final_end_time = time.time()
	 		print("Total characters processed in this translating lab {} are {} chars".format(lab,total_char))
	 		print("Total Translation time {} minutes".format((final_end_time-start_time)/60))
	 	end = time.time()
	 	print("Total execution time for all labs: {} hrs".format((end-begin)/3600))


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Machine language translations')
	parser.add_argument('--service',
					dest='service',
                   type=str, 
                   required=False,
                   help='Please mention which service(amazon/google) to use for translation')

	parser.add_argument('--model',
					dest='model',
                   type=str, 
                   required=False,
                   help='Please mention which model you want: (default/custom)')
	args = parser.parse_args()
	defaults = {
	'bucket_name':"hol-gaurav",
	'src_dir':'source',
	'dst_dir':'target'
	}
	print("Running the translate application using {} service and {} model".format(args.service, args.model))
	if args.service == 'google':
		trans  = Translate(bucket_name=defaults['bucket_name'], src_dir=defaults['src_dir'], dst_dir=defaults['dst_dir'], model = args.model)
		trans.main()
		# trans.upload_s3(src_dir=defaults['src_dir'], dst_dir=defaults['dst_dir'], bucket_name=defaults['bucket_name'], lab_name='hol-2044-01-ism_xml_all')
	if args.service == 'amazon':
		defaults = {
		'src_dir':"source",
		'dst_dir':"target",
		'src_lang':"en",
		'dst_lang':"es"
		}
		trans  = Atranslate(src_dir = defaults['src_dir'], dst_dir = defaults['dst_dir'], src_lang=defaults['src_lang'], dst_lang = defaults['dst_lang'])
		trans.main()
