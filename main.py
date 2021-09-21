# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @AUTHOR : njmck

import pandas as pd
import json
import collections
import re
from bs4 import BeautifulSoup
from urllib.request import urlopen
import ssl
import time



def article_url_list(main_url):
	'''
	Accepts the main page URL for Easy Japanese and returns a list of URLs
	of all the main news articles.
	'''
	# Access URL for all of yesterday's articles and process HTML:
	url = str(main_url)
	html_doc = urlopen(url, context=ssl._create_unverified_context())
	soup = BeautifulSoup(html_doc, 'html.parser')
	soup_pretty = soup.prettify()
	# Parse HTML for URLs for each individual news article:
	content = soup.find('div', attrs={'id': 'yesterday'})
	content1 = soup.find_all('a', attrs={'class': 'row no-margin item-recent '})
	# Additional articles are accessed separately after pressing the "View more" button:
	content2 = soup.find_all('a', attrs={'class': 'row no-margin item-recent news-more'})
	content_all = content1 + content2
	# Generate a list of URLs for all yesterday's articles:
	url_list = [i_0['href'] for i_0 in content_all]
	return url_list


def scrape_jlpt_vocab(url_list, sleep_time):
	'''
	Accepts the URL list from article_url_list() and compiles the vocabulary into a dictionary
	separated by URL and JLPT level.
	'''
	# Specify JLPT levels and initialise url dictionary to fill with vocabulary sorted by url:
	jlpt_levels = ['jlpt-n1', 'jlpt-n2', 'jlpt-n3', 'jlpt-n4', 'jlpt-n5']
	url_dict = {}
	# Access each article individually and store words in dictionary:
	for i_0 in url_list:
		html_doc = urlopen(i_0, context=ssl._create_unverified_context())
		soup = BeautifulSoup(html_doc, 'html.parser')
		content = soup.find('div', attrs={'class': 'content'})
		jlpt_vocab = {}
		for i_1 in jlpt_levels:
			jlpt_parent = content.find_all('span', attrs={'class': i_1})
			jlpt_main = []
			jlpt_kana = []
			for i_2 in jlpt_parent:
				if i_2.find('ruby'):
					jlpt_main.append(i_2.ruby.find(text=True, recursive=False))
					jlpt_kana.append(i_2.rt.find(text=True))
				else:
					jlpt_main.append(i_2.get_text())
					jlpt_kana.append(None)
			jlpt_vocab[i_1] = (jlpt_main, jlpt_kana)
		url_dict[i_0] = jlpt_vocab
		print('Processing url: ' + i_0)
		# Sleep between each article to save bandwidth or avoid IP address block:
		time.sleep(sleep_time)
	return url_dict


def wwwjdic_import(json_filename):
	'''
	Imports the WWJDIC Japanese-English json file as a dictionary.
	Up-to-date xml file for this can be found here:
	http://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project
	http://nihongo.monash.edu/wwwjdicinf.html#code_tag
	'''
	# Import json file of wwwjdic dictionary:
	with open(json_filename, 'r') as jsonfile:
		json_load = json.load(jsonfile)
	wwwjdic_json = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(json_load)
	return wwwjdic_json


def wwwjdic_jp(wwwjdic_dict):
	'''
	Generates a kanji list based on WWWJDIC.
	'''
	# Generate a kanji list containing kanji if it exists:
	jp_list = []
	for i in range(len(wwwjdic_dict)):
		child_list = []
		if 'k_ele' in wwwjdic_dict[i]:
			if isinstance(wwwjdic_dict[i]['k_ele'], dict):
				child_list.append(wwwjdic_dict[i]['k_ele']['keb'])
			else:
				for i_one in range(len(wwwjdic_dict[i]['k_ele'])):
					child_list.append(wwwjdic_dict[i]['k_ele'][i_one]['keb'])
		if isinstance(wwwjdic_dict[i]['r_ele'], dict):
			child_list.append(wwwjdic_dict[i]['r_ele']['reb'])
		else:
			for i_one in range(len(wwwjdic_dict[i]['r_ele'])):
				child_list.append(wwwjdic_dict[i]['r_ele'][i_one]['reb'])
		jp_list.append(child_list)
	return jp_list


def wwwjdic_kana(wwwjdic_dict):
	'''
	Generates a kana list based on WWWJDIC.
	'''
	# Generate a kana list:
	kana_list = []
	for i in range(len(wwwjdic_dict)):
		child_list = []
		if isinstance(wwwjdic_dict[i]['r_ele'], dict):
			child_list.append(wwwjdic_dict[i]['r_ele']['reb'])
		else:
			for i_one in range(len(wwwjdic_dict[i]['r_ele'])):
				child_list.append(wwwjdic_dict[i]['r_ele'][i_one]['reb'])
		kana_list.append(child_list)
	return kana_list


def wwwjdic_en(wwwjdic_dict):
	'''
	Generates a English definition list based on WWWJDIC.
	'''
	# Grab the English meanings too:
	en_list = []
	for i_0 in wwwjdic_dict:
		if isinstance(i_0['sense'], list):
			gloss_list = []
			for i_1 in i_0['sense']:
				if '#text' in i_1['gloss']:
					text_list = [i_1['gloss']['#text']]
				else:
					text_list = []
					for i_2 in i_1['gloss']:
						text_list.append(i_2['#text'])
				gloss_list.append(text_list)
		else:
			gloss_list = []
			if '#text' in i_0['sense']['gloss']:
				text_list  = [i_0['sense']['gloss']['#text']]
				gloss_list.append(text_list)
			else:
				text_list = []
				for i_1 in i_0['sense']['gloss']:
					text_list.append(i_1['#text'])
				gloss_list.append(text_list)
		en_list.append(gloss_list)
	return en_list


def wwwjdic_pos_info(wwwjdic_dict):
	'''
	Generates a 'position' list based on WWWJDIC.
	Position is the word type, such as Noun, Adjective, etc.
	'''
	# 'pos' determines the word type:
	pos_main_list = []
	for i_0 in wwwjdic_dict:
		if isinstance(i_0['sense'], list):
			pos_parent_list = []
			for i_1 in i_0['sense']:
				if 'pos' in i_1:
					if isinstance(i_1['pos'], list):
						pos_list = i_1['pos']
					else:
						pos_list = [i_1['pos']]
				pos_parent_list.append(pos_list)
		else:
			pos_parent_list = []
			if 'pos' in i_0['sense']:
				if isinstance(i_0['sense']['pos'], list):
					pos_list = i_0['sense']['pos']
				else:
					pos_list = [i_0['sense']['pos']]
			pos_parent_list.append(pos_list)
		pos_main_list.append(pos_parent_list)
	return pos_main_list


def wwwjdic_misc_info(wwwjdic_dict):
	'''
	Generates a 'miscellaneous' list based on WWWJDIC.
	Misc is miscellaneous information such as 'usually kana' or 'colloquialism'.
	'''
	# misc field:
	misc_main_list = []
	for i_0 in wwwjdic_dict:
		if isinstance(i_0['sense'], list):
			misc_parent_list = []
			for i_1 in i_0['sense']:
				if 'misc' in i_1:
					if isinstance(i_1['misc'], list):
						misc_list = i_1['misc']
					else:
						misc_list = [i_1['misc']]
				else:
					misc_list = []
				misc_parent_list.append(misc_list)
		else:
			misc_parent_list = []
			if 'misc' in i_0['sense']:
				if isinstance(i_0['sense']['misc'], list):
					misc_list = i_0['sense']['misc']
				else:
					misc_list = [i_0['sense']['misc']]
			else:
				misc_list = []
			misc_parent_list.append(misc_list)
		misc_main_list.append(misc_parent_list)
	return misc_main_list


def wwwjdic_field_info(wwwjdic_dict):
	'''
	Generates a 'field' list based on WWWJDIC.
	Field denotes whether the word relates to a specific field of study such as biology, sport, etc.
	'''
	field_main_list = []
	for i_0 in wwwjdic_dict:
		if isinstance(i_0['sense'], list):
			field_parent_list = []
			for i_1 in i_0['sense']:
				if 'field' in i_1:
					if isinstance(i_1['field'], list):
						field_list = i_1['field']
					else:
						field_list = [i_1['field']]
				else:
					field_list = []
				field_parent_list.append(field_list)
		else:
			field_parent_list = []
			if 'field' in i_0['sense']:
				if isinstance(i_0['sense']['field'], list):
					field_list = i_0['sense']['field']
				else:
					field_list = [i_0['sense']['field']]
			else:
				field_list = []
			field_parent_list.append(field_list)
		field_main_list.append(field_parent_list)
	return field_main_list


def wwwjdic_sense_info(wwwjdic_dict):
	'''
	Generates a 's_inf' list based on WWWJDIC.
	Denotes usage information in a practical context (kanji usage, nuances, etc.)
	'''
	s_inf_main_list = []
	for i_0 in wwwjdic_dict:
		if isinstance(i_0['sense'], list):
			s_inf_parent_list = []
			for i_1 in i_0['sense']:
				if 's_inf' in i_1:
					if isinstance(i_1['s_inf'], list):
						s_inf_list = i_1['s_inf']
					else:
						s_inf_list = [i_1['s_inf']]
				else:
					s_inf_list = []
				s_inf_parent_list.append(s_inf_list)
		else:
			s_inf_parent_list = []
			if 's_inf' in i_0['sense']:
				if isinstance(i_0['sense']['s_inf'], list):
					s_inf_list = i_0['sense']['s_inf']
				else:
					s_inf_list = [i_0['sense']['s_inf']]
			else:
				s_inf_list = []
			s_inf_parent_list.append(s_inf_list)
		s_inf_main_list.append(s_inf_parent_list)
	return s_inf_main_list


tag_dict = {
			"MA;": "martial arts term",
			"X;": "rude or X-rated term",
			"abbr;": "abbr",
			"adj-i;": "い-adj",
			"adj-ix;": "い-adj",
			"adj-na;": "な-adj",
			"adj-no;": "の-adj",
			"adj-pn;": "pre-noun adjectival (連体詞)",
			"adj-t;": "`taru' adjective",
			"adj-f;": "noun or verb acting prenominally",
			"adv;": "adverb (副詞)",
			"adv-to;": "と-adverb",
			"arch;": "archaism",
			"ateji;": "ateji reading (当て字)",
			"aux;": "auxiliary",
			"aux-v;": "auxiliary verb",
			"aux-adj;": "auxiliary adjective",
			"Buddh;": "Buddhist term",
			"chem;": "chemistry term",
			"chn;": "children's language",
			"col;": "colloquialism",
			"comp;": "computer terminology",
			"conj;": "conjunction",
			"cop;": "copula",
			"ctr;": "counter",
			"derog;": "derogatory",
			"eK;": "exclusively kanji",
			"ek;": "exclusively kana",
			"exp;": "expressions (phrases, clauses, etc.)",
			"fam;": "familiar language",
			"fem;": "female term or language",
			"food;": "food term",
			"geom;": "geometry term",
			"gikun;": "gikun (meaning as reading) or jukujikun (special kanji reading)",
			"hon;": "honorific language (尊敬語)",
			"hum;": "humble language (謙譲語)",
			"iK;": "word containing irregular kanji usage",
			"id;": "idiomatic expression",
			"ik;": "word containing irregular kana usage",
			"int;": "interjection (感動詞)",
			"io;": "irregular okurigana usage",
			"iv;": "irregular verb",
			"ling;": "linguistics terminology",
			"m-sl;": "manga slang",
			"male;": "male term or language",
			"male-sl;": "male slang",
			"math;": "mathematics",
			"mil;": "military",
			"n;": "noun (普通名詞)",
			"n-adv;": "adverbial noun (副詞的名詞)",
			"n-suf;": "noun, used as a suffix",
			"n-pref;": "noun, used as a prefix",
			"n-t;": "noun (temporal) (時相名詞)",
			"num;": "numeric",
			"oK;": "word containing out-dated kanji",
			"obs;": "obsolete term",
			"obsc;": "obscure term",
			"ok;": "out-dated or obsolete kana usage",
			"oik;": "old or irregular kana form",
			"on-mim;": "onomatopoeic or mimetic word",
			"pn;": "pronoun",
			"poet;": "poetical term",
			"pol;": "polite language (丁寧語)",
			"pref;": "prefix",
			"proverb;": "proverb",
			"prt;": "particle",
			"physics;": "physics terminology",
			"quote;": "quotation",
			"rare;": "rare",
			"sens;": "sensitive",
			"sl;": "slang",
			"suf;": "suffix",
			"uK;": "word usually written using kanji alone",
			"uk;": "usu. kana",
			"unc;": "unclassified",
			"yoji;": "yojijukugo",
			"v1;": "Ichidan verb",
			"v1-s;": "Ichidan verb - kureru special class",
			"v2a-s;": "Nidan verb with 'u' ending (archaic)",
			"v4h;": "Yodan verb with `hu/fu' ending (archaic)",
			"v4r;": "Yodan verb with `ru' ending (archaic)",
			"v5aru;": "Godan verb - -aru special class",
			"v5b;": "Godan verb with `bu' ending",
			"v5g;": "Godan verb with `gu' ending",
			"v5k;": "Godan verb with `ku' ending",
			"v5k-s;": "Godan verb - Iku/Yuku special class",
			"v5m;": "Godan verb with `mu' ending",
			"v5n;": "Godan verb with `nu' ending",
			"v5r;": "Godan verb with `ru' ending",
			"v5r-i;": "Godan verb with `ru' ending (irregular verb)",
			"v5s;": "Godan verb with `su' ending",
			"v5t;": "Godan verb with `tsu' ending",
			"v5u;": "Godan verb with `u' ending",
			"v5u-s;": "Godan verb with `u' ending (special class)",
			"v5uru;": "Godan verb - Uru old class verb (old form of Eru)",
			"vz;": "Ichidan verb - zuru verb (alternative form of -jiru verbs)",
			"vi;": "intransitive verb",
			"vk;": "Kuru verb - special class",
			"vn;": "irregular nu verb",
			"vr;": "irregular ru verb, plain form ends with -ri",
			"vs;": "noun as する-verb",
			"vs-c;": "su verb - precursor to the modern suru",
			"vs-s;": "suru verb - special class",
			"vs-i;": "suru verb - included",
			"kyb;": "Kyoto-ben",
			"osb;": "Osaka-ben",
			"ksb;": "Kansai-ben",
			"ktb;": "Kantou-ben",
			"tsb;": "Tosa-ben",
			"thb;": "Touhoku-ben",
			"tsug;": "Tsugaru-ben",
			"kyu;": "Kyuushuu-ben",
			"rkb;": "Ryuukyuu-ben",
			"nab;": "Nagano-ben",
			"hob;": "Hokkaido-ben",
			"vt;": "transitive verb",
			"vulg;": "vulgar expression or word",
			"adj-kari;": "`kari' adjective (archaic)",
			"adj-ku;": "`ku' adjective (archaic)",
			"adj-shiku;": "`shiku' adjective (archaic)",
			"adj-nari;": "archaic/formal form of na-adjective",
			"n-pr;": "proper noun",
			"v-unspec;": "verb unspecified",
			"v4k;": "Yodan verb with `ku' ending (archaic)",
			"v4g;": "Yodan verb with `gu' ending (archaic)",
			"v4s;": "Yodan verb with `su' ending (archaic)",
			"v4t;": "Yodan verb with `tsu' ending (archaic)",
			"v4n;": "Yodan verb with `nu' ending (archaic)",
			"v4b;": "Yodan verb with `bu' ending (archaic)",
			"v4m;": "Yodan verb with `mu' ending (archaic)",
			"v2k-k;": "Nidan verb (upper class) with `ku' ending (archaic)",
			"v2g-k;": "Nidan verb (upper class) with `gu' ending (archaic)",
			"v2t-k;": "Nidan verb (upper class) with `tsu' ending (archaic)",
			"v2d-k;": "Nidan verb (upper class) with `dzu' ending (archaic)",
			"v2h-k;": "Nidan verb (upper class) with `hu/fu' ending (archaic)",
			"v2b-k;": "Nidan verb (upper class) with `bu' ending (archaic)",
			"v2m-k;": "Nidan verb (upper class) with `mu' ending (archaic)",
			"v2y-k;": "Nidan verb (upper class) with `yu' ending (archaic)",
			"v2r-k;": "Nidan verb (upper class) with `ru' ending (archaic)",
			"v2k-s;": "Nidan verb (lower class) with `ku' ending (archaic)",
			"v2g-s;": "Nidan verb (lower class) with `gu' ending (archaic)",
			"v2s-s;": "Nidan verb (lower class) with `su' ending (archaic)",
			"v2z-s;": "Nidan verb (lower class) with `zu' ending (archaic)",
			"v2t-s;": "Nidan verb (lower class) with `tsu' ending (archaic)",
			"v2d-s;": "Nidan verb (lower class) with `dzu' ending (archaic)",
			"v2n-s;": "Nidan verb (lower class) with `nu' ending (archaic)",
			"v2h-s;": "Nidan verb (lower class) with `hu/fu' ending (archaic)",
			"v2b-s;": "Nidan verb (lower class) with `bu' ending (archaic)",
			"v2m-s;": "Nidan verb (lower class) with `mu' ending (archaic)",
			"v2y-s;": "Nidan verb (lower class) with `yu' ending (archaic)",
			"v2r-s;": "Nidan verb (lower class) with `ru' ending (archaic)",
			"v2w-s;": "Nidan verb (lower class) with `u' ending and `we' conjugation (archaic)",
			"archit;": "architecture term",
			"astron;": "astronomy, etc. term",
			"baseb;": "baseball term",
			"biol;": "biology term",
			"bot;": "botany term",
			"bus;": "business term",
			"econ;": "economics term",
			"engr;": "engineering term",
			"finc;": "finance term",
			"geol;": "geology, etc. term",
			"law;": "law, etc. term",
			"mahj;": "mahjong term",
			"med;": "medicine, etc. term",
			"music;": "music term",
			"Shinto;": "Shinto term",
			"shogi;": "shogi term",
			"sports;": "sports term",
			"sumo;": "sumo term",
			"zool;": "zoology term",
			"joc;": "jocular, humorous term",
			"anat;": "anatomical term",
			"Christn;": "Christian term",
			"net-sl;": "Internet slang",
			"dated;": "dated term",
			"hist;": "historical term",
			"lit;": "literary or formal term",
			"litf;": "literary or formal term",
			"surname;": "family or surname",
			"place;": "place name",
			"unclass;": "unclassified name",
			"company;": "company name",
			"product;": "product name",
			"work;": "work of art, literature, music, etc. name",
			"person;": "full name of a particular person",
			"given;": "given name or forename, gender not specified",
			"station;": "railway station",
			"organization;": "organization name"
			}


def wwwjdic_en_neat(en_list, pos_main_list, misc_main_list, field_main_list, s_inf_main_list):
	'''
	Neatens the nested lists from the wwwjdic_en() function into a human-readable format with
	other useful information embedded.
	'''
	global tag_dict
	# Make the final strings:
	en_list_neat = []
	for i_0 in range(len(en_list)):
		# 'pos'
		gloss_num = 1
		gloss_main_list = []
		for i_1 in range(len(en_list[i_0])):
			unabbr_pos_list = [tag_dict[i_2] for i_2 in pos_main_list[i_0][i_1]]
			if i_1 > 0:
				if pos_main_list[i_0][i_1] != pos_main_list[i_0][i_1 - 1]:
					pos_str = '<b>' + ', '.join(unabbr_pos_list) + ':|' + '</b>'
				else:
					pos_str = ''
			else:
				pos_str = '<b>' + ', '.join(unabbr_pos_list) + ':|' + '</b>'
			# Make list of misc, field, and s_inf:
			tags_list = misc_main_list[i_0][i_1] + field_main_list[i_0][i_1]
			tags_list = [tag_dict[i_2] for i_2 in tags_list]
			tags_list += s_inf_main_list[i_0][i_1]
			tags_list = ' (' + ', '.join(tags_list) + ')'
			if tags_list == ' ()':
				gloss_str = str(gloss_num) + '. ' + '; '.join(en_list[i_0][i_1])
			else:
				gloss_str = str(gloss_num) + '. ' + '; '.join(en_list[i_0][i_1]) + tags_list
			gloss_main_list.append(pos_str + gloss_str)
			gloss_num += 1
		en_list_neat.append("|".join(gloss_main_list))
	return en_list_neat


def nested_list_len(ls):
	'''
	Takes a list of lists, ensures they are of equal length, and converts it to a dataframe.
	'''
	equal = True
	if isinstance(ls, list) and len(ls) > 1:
		first_len = len(ls[0])
		for i_0 in ls[1:]:
			if len(i_0) != first_len:
				equal = False
		return equal
	else:
		raise Exception('Argument must be a list of length > 1.')


def wwwjdic_make_df(jp_list, kana_list, en_list, en_list_neat, pos_main_list, misc_main_list, field_main_list, s_inf_main_list):
	'''
	Generates a dataframe from WWWJDIC information.
	'''
	lists_to_df = [
				   jp_list,
				   kana_list,
				   en_list,
				   en_list_neat,
				   pos_main_list,
				   misc_main_list,
				   field_main_list,
				   s_inf_main_list
				   ]
	col_names = ["jp", "kana", "en", "en_neat", "pos", "misc", "field", "s_inf"]
	if nested_list_len(lists_to_df):
		wwwjdic_df = pd.DataFrame(lists_to_df).transpose()
		wwwjdic_df.columns = col_names
	else:
		print('Dataframes not of equal length:')
		for i_0 in lists_to_df:
			print(len(i_0))
		wwwjdic_df = None
	return wwwjdic_df


def multi_match_handler(vocab, potential_list):
	'''
	Accepts a list of potential matches.
	Allows the user to pick the most appropriate solution.
	'''
	print("Multiple matches found. Which definition is most correct for:")
	print(vocab + "?:")
	for num, i_2 in enumerate(potential_list):
		print('----------[' + str(num + 1) + ']----------')
		print(wwwjdic_jp_list[i_2])
		print_eng = re.sub('<b>', '', wwwjdic_en_neat_list[i_2])
		print_eng = re.sub('</b>', '', print_eng)
		print_eng = re.sub('\|', '\n', print_eng)
		print('   ' + print_eng)
		print()
	try:
		user_choice = int(input()) - 1
	except ValueError:
		user_choice = None
	if user_choice != None:
		# If user choice index is out of range, don't continue:
		if user_choice >= len(potential_list) or not isinstance(user_choice, int):
			while user_choice >= len(potential_list):
				user_choice = int(input()) - 1
	# Append the user's choice:
	index = potential_list[user_choice]
	return index


def index_match(vocab, secondary_vocab):
	'''
	Accepts a list of vocabulary and determines which definition is the match
	from the WWWJDIC Japanese-English dictionary.
	It may ask the user to use their own judgement and choose using multi_match_handler.
	Returns None if no match found.
	'''
	global wwwjdic_jp_list, wwwjdic_kana_list, wwwjdic_en_neat_list
	if secondary_vocab == None:
		secondary_vocab = vocab
	potential_list = []
	# Create a list of potential matches from WWWJDIC:
	for i_1 in range(len(wwwjdic_jp_list)):
		if vocab in wwwjdic_jp_list[i_1]:
			potential_list.append(i_1)
	if potential_list == []:
		for i_1 in range(len(wwwjdic_kana_list)):
			if vocab in wwwjdic_kana_list[i_1]:
				potential_list.append(i_1)
	# Determine which meaning is correct based on both primary and secondary vocab:
	if len(potential_list) == 1:
		index = potential_list[0]
	else:
		likely_list = []
		for i_1 in potential_list:
			if vocab != secondary_vocab:
				if vocab and secondary_vocab in wwwjdic_jp_list[i_1]:
					likely_list.append(i_1)
			else:
				if vocab in wwwjdic_jp_list[i_1]:
					likely_list.append(i_1)
		# Switch to potential_list candidates if no matches in likely_list:
		if len(likely_list) == 1:
			index = likely_list[0]
		elif len(likely_list) > 1:
			index = multi_match_handler(vocab, likely_list)
		elif likely_list == [] and len(potential_list) == 1:
			index = potential_list[0]
		elif likely_list == [] and len(potential_list) > 1:
			index = multi_match_handler(vocab, potential_list)
		else:
			index = None
	return index


def jlpt_vocab_dict(url_dict, wwwjdic_en_neat_list):
	'''
	Creates a dictionary of vocab from all articles with the JLPT level as the key, and includes
	necessary information for Japanese-English flashcards.
	'''
	jlpt_study_levels = ['jlpt-n1', 'jlpt-n2', 'jlpt-n3', 'jlpt-n4', 'jlpt-n5']
	vocab_dict = {jlpt_lvl: {'main': [], 'kana': [], 'en_neat': [], 'url': []} for jlpt_lvl in jlpt_study_levels}
	for jlpts in jlpt_study_levels: # For each of the two 'jlptn1' and 'jlptn2':
		for urls in url_dict: # For each URL in url_dict (28):
			for num, mains in enumerate(url_dict[urls][jlpts][0]): # For each word ['進行']:
				main_query = index_match(mains, url_dict[urls][jlpts][1][num]) # Find the index of the individual word '31620'
				if main_query != None: # If it didn't return a None value:
					# Main:
					vocab_dict[jlpts]['main'].append(mains)
					# Kana
					kana = url_dict[urls][jlpts][1][num]
					vocab_dict[jlpts]['kana'].append(kana)
					# Eng:
					en_neat = wwwjdic_en_neat_list[main_query]
					vocab_dict[jlpts]['en_neat'].append(en_neat)
					# Url:
					url_str = "<a href=\"" + urls + "\">Article URL</a>"
					vocab_dict[jlpts]['url'].append(url_str)
	return vocab_dict


def export_flashcards(vocab_dict, yesterday_date):
	'''
	Converts the vocab dictionary into a Pandas dataframe and exports to separate Excel files
	based on JLPT level.
	'''
	jlpt_study_levels = ('jlpt-n1', 'jlpt-n2', 'jlpt-n3', 'jlpt-n4', 'jlpt-n5')
	filenames = [(yesterday_date + '_' + i_0 + '.xlsx') for i_0 in jlpt_study_levels]
	for num, i_0 in enumerate(filenames):
		vocab_df = pd.DataFrame.from_dict(vocab_dict[jlpt_study_levels[num]])
		colname_list = ["Text 1", "Text 2", "Text 3", "Text 4"]
		vocab_df.columns = colname_list
		vocab_df.to_excel(i_0, sheet_name='Sheet1', index=False)
	print("Files exported.")


# MAIN SCRIPT STARTS HERE:
# Web scrape Easy Japanese news:
yesterday_date = '2021.09.19'
url_list = article_url_list("http://easyjapanese.net/news/normal/all?hl=en-US")
url_dict = scrape_jlpt_vocab(url_list, 1) # Time delay in seconds to access each article.

# Use the WWWJDIC dictionary to generate dataframes and lists of definitions:
wwwjdic_dict = wwwjdic_import("wwwjdic.json")
jp_list = wwwjdic_jp(wwwjdic_dict)
kana_list = wwwjdic_kana(wwwjdic_dict)
en_list = wwwjdic_en(wwwjdic_dict)
pos_main_list = wwwjdic_pos_info(wwwjdic_dict)
misc_main_list = wwwjdic_misc_info(wwwjdic_dict)
field_main_list = wwwjdic_field_info(wwwjdic_dict)
s_inf_main_list = wwwjdic_sense_info(wwwjdic_dict)
en_list_neat = wwwjdic_en_neat(en_list, pos_main_list, misc_main_list, field_main_list, s_inf_main_list)
wwwjdic_df = wwwjdic_make_df(jp_list, kana_list, en_list, en_list_neat, pos_main_list, misc_main_list, field_main_list, s_inf_main_list)

wwwjdic_jp_list = wwwjdic_df['jp'].tolist()
wwwjdic_kana_list = wwwjdic_df['kana'].tolist()
wwwjdic_en_neat_list = wwwjdic_df['en_neat'].tolist()

vocab_dict = jlpt_vocab_dict(url_dict, wwwjdic_en_neat_list)
export_flashcards(vocab_dict, yesterday_date)
