
# Watchful Eyes Ban Bot v.2 by u/BuckRowdy 

# Import modules
import praw
import pmtw
import time
from time import localtime, timezone
from datetime import datetime as datetime, timedelta as td, date, timezone
import config
import traceback
import sys
import re

##################################
# Define Variables

# Define ths sub to work on.  Usernotes will not work accurately on r/mod.  Each sub must be listed individually.
# Sub names are defined in the config file. 
sub_name = 'politicalhumor+news+marchagainstnazis'
toxic_subs = "shitredditsays+shitpoliticssays+conservative+declineintocensorship+watchredditdie+subredditdrama+anarcho_capitalism+banned+genzedong"



# Number of seconds to sleep between scans
sleep_seconds = 30

# Sub to log bans and admin actions.  Admin removals and bans by this account will be logged in the sub.
submit_sub = "submanagerbot"

# Set up a time period for the last pass of the bot for checking timestamps on items.  
right_now = time.time()
last_pass = (right_now  - 45)


# Define your ban notes here.  These are for the ban note in the upper right corner of modmail in red.
# Both fields are editable, but you must use the letters in the first column in your report reason.
# Report reasons always start with 'ban' followed by the time then the code for the reason.  
# A 30 day ban for trolling would read as follows: ban 30 t
# Permanent bans are input as 0.  So a perm ba for covid misinfo would be ban 0 c

ban_macros = 			{ 	'c' : 'Covid Misinfo',
							'v' : 'Violent Content',
							'r' : 'Bigotry/Racism',
							't' : 'Trolling',
							's' : 'Spam',
							'm' : 'Misinformation',
							'd' : 'Dehumanizing Speech',
							'n' : 'Nazi',
							'b' : 'Brigading',
							'h' : 'Hate Speech',
							'a' : 'Antagonizing/Rude'						
						}

###  Defines the reddit login function
### A refresh token is used so you can maintain 2FA on the bot account.
### Login items stored in a config.py file and imported.
def reddit_login():
 
	try:
		reddit = praw.Reddit(   
								user_agent = config.user_agent,
								client_id = config.client_id,
								client_secret = config.client_secret,
								refresh_token = config.refresh_token
							)

	except Exception as e:
		print(f'\t### ERROR - Could not login.\n\t{e}')
	print(f'Logged in as: {reddit.user.me()}\n\n')
	return reddit


# Process ModQueue comments and submissions for the ban phrase.

def ban_on_phrase(subreddit):
	try: 
		
		start_time = datetime.fromtimestamp(right_now).strftime('%a, %b %d, %Y at %H:%M:%S')
		ban_phrase = 'ban'
		###  Process Comments
		# Prints the ban syntax to the terminal so you can easily reference.
		print('~~~~~~~~~~~~~~')
		print('Starting up...')
		print('Ban syntax:\nban <days> [macro]\n<0> days for perm\n\nReport reasons:\n[c] Covid\n[a] Rude/Antagonizing\n[v] Violence\n[s] Spam\n[r] Racism/Bigotry\n[t] Trolling\n[m] Misinformation\n[d] Dehumanizing speech\n[n] Nazi\n[b] Brigading\n[h] Hate Speech\n\n')
		for item in subreddit.mod.modqueue(limit=None):
				
			# T1 is reddit's code for comment objects.
			if item.fullname.startswith("t1_") and len(item.mod_reports):
				item_type = 'Comment'
				
				# Ban message field has a 1000 character limit so quoted comments need to be sliced to prevent api errors.
				comment_slice = f'{item.body}'
				replace_comment = comment_slice[:300]

				# Takes multi line comment and joins it so it can be properly formatted when linked.
				sliced_comment = ''.join(f'{i}' for i in replace_comment.split('\n\n'))
				#Set up a ban header and footer
				ban_header = f'This **{item_type}** may have fully or partially contributed to your ban:\n\n'
				ban_footer = f'**[^(Context)]({item.permalink}?context=9)** ¯¯ **[^(r/{item.subreddit} rules)](http://www.reddit.com/r/{item.subreddit}/about/rules)** ¯¯ **[^(Reddit Content Policy)](https://www.redditinc.com/policies/content-policy)**\n\n'
			
				# Set up a comment quote syntax. 
				comment_quote = f'\n> [{sliced_comment}...]({item.permalink})\n\n'

				# Go through the mod reports and parse the info for ban details.
				for report_reason, mod_name in item.mod_reports:
					if ban_phrase in report_reason:
						items = report_reason.split(" ")
						ban_length = int(items[1])
						ban_reason_raw = items[2]
						ban_reason = ban_reason_raw.lower()
						
						# Ban note is a field in the /about/banned page as well as in modmail and modlog. 
						# Here, the ban note is taken from a user defined dictionary. 
						ban_note = ban_macros[ban_reason]
						print('\nMod report found...')
						time.sleep(1)
						print(f'r/{item.subreddit} | {mod_name}: {report_reason}')
						 
						if len(items) > 1:
							if items[0] == 'ban':
								item.mod.remove()
								item.mod.lock()
								print(f"REMOVE ITEM {item.fullname} ## {item.permalink}")
								ban_sub = item.subreddit.display_name

								# Ban length of 0 for permanent bans, any other digit will trigger a temp ban.
								if ban_length == 0:
									if ban_reason in ban_macros:
										ban_note = ban_macros[ban_reason]
										ban_message = '**'+ban_note+'**\n\n'+ban_header+comment_quote+ban_footer
										reddit.subreddit(ban_sub).banned.add(
																				f'{item.author}', 
																				ban_reason=f'{ban_note} - {mod_name}', 
																				ban_message=f'{ban_message}', 
																				note=f'{item.permalink}'
																				)										
										
										print(f"{mod_name} banned {item.author} permanently.")

										# Create and post a usernotes object for this item.
										notes = pmtw.Usernotes(reddit, item.subreddit)
										n = pmtw.Note(
														user=f'{item.author}', 
														note=f'{ban_note} - {mod_name}',
														link=f'{item.permalink}',
														warning='ban'
														)
										notes.add_note(n)
										
								# Temp ban duration.
								elif ban_length > 0:
									if ban_reason in ban_macros:
										ban_note = ban_macros[ban_reason]
										ban_message = '**'+ban_note+'**\n\n'+ban_header+comment_quote+ban_footer
										reddit.subreddit(ban_sub).banned.add(
																				f'{item.author}', 
																				ban_reason=f'{ban_note} - {mod_name}', 
																				duration=ban_length, 
																				ban_message=f'{ban_message}', 
																				note=f'{item.permalink}'
																				)

										print(f"{mod_name} banned {item.author} for {ban_length} days.")
										notes = pmtw.Usernotes(reddit, item.subreddit)
										n = pmtw.Note(
														user=f'{item.author}', 
														note=f'{ban_length}d - {ban_note} - {mod_name}',
														link=f'{item.permalink}',
														warning='ban'
														)
										notes.add_note(n)
										
			###  Process Submissions 

			if item.fullname.startswith("t3_") and len(item.mod_reports):
				notes = pmtw.Usernotes(reddit, item.subreddit)
				item_type = 'Submission'
				ban_header = f'This **{item_type}** may have fully or partially contributed to your ban:\n\n'
				ban_footer = f'**[^(Context)]({item.permalink}?context=9)** ¯¯ **[^(r/{item.subreddit} rules)](http://www.reddit.com/r/{item.subreddit}/about/rules)** ¯¯ **[^(Reddit Content Policy)](https://www.redditinc.com/policies/content-policy)**\n\n'
				post_quote = f'\n> [{item.title}]({item.url})\n\n---\n\n'

				for report_reason, mod_name in item.mod_reports:
					if ban_phrase in report_reason:
						items = report_reason.split(" ")
						ban_length = int(items[1])
						ban_reason_raw = items[2]
						ban_reason = ban_reason_raw.lower()
						ban_note = ban_macros[ban_reason]
						print('Mod report found...')
						time.sleep(1)
						print(f'r/{item.subreddit} | {mod_name}: {report_reason}')
						time.sleep(1) 
		
						if len(items) > 1:
							if items[0] == 'ban':
								item.mod.remove()
								item.mod.lock()
								print(f"REMOVE ITEM {item.fullname} ## {item.permalink}")
								ban_sub = item.subreddit.display_name								

								if ban_length == 0:
									if ban_reason in ban_macros:
										ban_note = ban_macros[ban_reason]
										ban_message = '**'+ban_note+'**\n\n'+ban_header+post_quote+ban_footer
										reddit.subreddit(ban_sub).banned.add(
																				f'{item.author}', 
																				ban_reason=f'{ban_note} - {mod_name}', 
																				ban_message=f'{ban_message}', 
																				note=f'{item.permalink}'
																				)
										
										print(f"{mod_name} banned {item.author} permanently.")
										notes = pmtw.Usernotes(reddit, item.subreddit)
										n = pmtw.Note(
												user=f'{item.author}', 
												note=f'{ban_note} - {mod_name}',
												link=f'{item.permalink}',
												warning='ban'
												)
										notes.add_note(n)
										
								elif ban_length > 0:
									if ban_reason in ban_macros:
										ban_note = ban_macros[ban_reason]
										ban_message = '**'+ban_note+'**\n\n'+ban_header+post_quote+ban_footer
										reddit.subreddit(ban_sub).banned.add(
																				f'{item.author}', 
																				ban_reason=f'{ban_note} - {mod_name}', 
																				duration=ban_length, 
																				ban_message=f'{ban_message}', 
																				note=f'{item.permalink}'
																				)
										
										print(f"{mod_name} banned {item.author} for {ban_length} days.")
										notes = pmtw.Usernotes(reddit, item.subreddit)
										n = pmtw.Note(
														user=f'{item.author}', 
														note=f'{ban_length}d - {ban_note} - {mod_name}',
														link=f'{item.permalink}',
														warning='ban'
														)
										notes.add_note(n)
										
								
	except KeyboardInterrupt:
			print('\nShutting down....')
			sys.exit(1)
	except Exception as e:
			print(f'\t### ERROR - Something went wrong processing the modqueue.\n\t{e}')
			traceback.print_exc()					
	

#  This functions logs bans and admin level actions to a private log sub.  The list of monitored subs is smaller because other bots are logging for other subs.
def check_mod_log(subreddit):
	right_now = time.time()
	last_pass = (right_now  - 45)
		
	try:
		reddit.validate_on_submit = True
		for log in reddit.subreddit(sub_name).mod.log(mod="a"):
			time_stamp = datetime.fromtimestamp(int(log.created_utc)).strftime('%a, %b %d, %Y at %H:%M:%S')
			if log.created_utc <= last_pass:
				break
			else :
				log_post_selftext = f"Sub: r/{log.subreddit}\n\nAction: {log.action}\n\nMod: {log.mod}\n\nWhen: {time_stamp}\n\n---\n\nTitle: {log.target_title}\n\nTarget Author: u/{log.target_author}\n\nBody: {log.target_body}\n\nDetails: {log.details}\n\nDescription: {log.description}\n\n*[Link to item](http://reddit.com{log.target_permalink})* | [Subreddit modlog](http://reddit.com/r/{log.subreddit}/about/log)\n\n^(Links to ban items are not functional, view mod log instead.)"
				admin_log_post_title = f"Admin action '{log.action}' performed by u/{log.mod} in r/{log.subreddit}"
				reddit.subreddit(submit_sub).submit(admin_log_post_title, log_post_selftext)
				print(f"Action: >{log.action}< in r/{log.subreddit} was posted in r/submanagerbot.")

		for log in reddit.subreddit(sub_name).mod.log(limit = None):
			if log.created_utc <= last_pass:
				break

			if log.action == 'banuser':
			#if log.action == 'banuser' and log.subreddit == 'news':
				log_description = log.description.rsplit(' ',1)
				ban_reason_raw = log.description.split('-',1)
				ban_reason = ban_reason_raw[0]
				if ban_reason is not None:
					description = log_description[1]
					date_stamp = datetime.fromtimestamp(int(log.created_utc)).strftime('%m/%d/%y')
					log_post_selftext = f"Sub: r/{log.subreddit}\n\nAction: {log.action}\n\nMod: {log.mod}\n\nWhen: {time_stamp}\n\n---\n\nTitle: {log.target_title}\n\nTarget Author: u/{log.target_author}\n\nBody: {log.target_body}\n\nDetails: {log.details}\n\nLog Description: {log.description}\n\nPermalink: {description}\n\n[*Subreddit modlog*](http://reddit.com/r/{log.subreddit}/about/log)\n\n" #^(Links to ban items are not functional, view mod log instead.)"
					log_post_title = f"User u/{log.target_author} banned by u/{log.mod} in r/{log.subreddit} on {date_stamp}. Note: {ban_reason}"
					reddit.subreddit(submit_sub).submit(log_post_title, log_post_selftext)
					print(f"Action: >{log.action}< in r/{log.subreddit} was posted in r/submanagerbot.")
			else:
				continue
					        
	except KeyboardInterrupt:
			print('\nShutting down....')
			sys.exit(1)
	except Exception as e:
		print(f'\t### ERROR - Could not process mod log.\n\t{e}')
		traceback.print_exc()


# Check the mod log for threads removed in the past day and log their fullnames for removing reported comments. 
def report_remove_gather(subreddit):
	links_list = []
	# Saves a copy as a text file in case it needs to be referenced. 
	with open("/home/pi/bots/news/links_list.txt", "w+") as f:
		print("Compiling list of removed threads....")
		#right_now = time.time()
		removal_epoch = (right_now - 60*60*24)
		for log_item in reddit.subreddit(sub_name).mod.log(limit = 1000):
			if log_item.created_utc >= removal_epoch:			
				if log_item.action == 'removelink':
					if log_item.mod != 'AutoModerator':						
						logged_item = log_item.target_fullname
						if logged_item not in links_list:
							links_list.append(str(logged_item))							
		f.write(f"{links_list}")	
		return links_list				
	f.close()
	print("Done listing removed threads...")



# Check for reported comments in removed threads and remove them. 
def report_cleanser(links_list):
	try:
		print("Looking for reports on removed threads....")
		if len(links_list) > 0:
				print('Okay. Checking reports on removed posts...')
				for item in reddit.subreddit(sub_name).mod.reports(limit = 1000):
					if item.fullname.startswith("t1_"):
						if item.link_id in links_list:
							item.mod.remove()
							print(f'REMOVE ITEM: r/{item.subreddit} {item.permalink}')
		else:
			print('None found')
		print("Done removing any reported comments in removed threads....")
	except KeyboardInterrupt:
			print('\nShutting down....')
			sys.exit(1)
	except Exception as e:
		print(f'\t### ERROR - Too many reports in queue.\n\t{e}')
		traceback.print_exc()	

			
## This function checks the modqueue and implements various custom micro conditions to reduce workload.
def micro_conditions(subreddit):
	print('Checking for reported AutoModerator comments...')
	try:
		for item in reddit.subreddit(sub_name).mod.reports(limit = None):
			
			# This check removes reported comments with 'tard' phrases in them.
			if item.fullname.startswith("t1_"):
				report_body = item.body
				ableism_search = re.match(r'(?i)(fuck|trump|vaxx|lib|re|conserva)tards?', report_body)
				
				if not ableism_search is None:
					#if ableism_search in report_body:
					item.mod.remove()
					print(f"REMOVE ITEM: {item.fullname}  {item.permalink}")

			#  Approve any reported comments by automoderator. 
			if item.author == 'AutoModerator':
			#if item.author_fullname == 't2_6l4z3':
				item.mod.approve()
				print('Approved AutoMod comment')
			
	except KeyboardInterrupt:
			print('\nShutting down....')
			sys.exit(1)
	except Exception as e:
		print("\t\n### ERROR - You\'re a terrible coder.")
		traceback.print_exc()


def meta_sub_check(toxic_subs):

	try:
		for submission in reddit.subreddit(toxic_subs).new(limit = 100):
			time_stamp = datetime.fromtimestamp(int(submission.created_utc)).strftime('%a, %b %d, %Y at %H:%M:%S')
			linked_post = submission.url
			linked_title = submission.title
			post_author = submission.author.name
			news_post = re.search(r'r/news', linked_post)
			news_title = re.search(r'r/news', linked_title)
			ban_check = any(reddit.subreddit(submit_sub).banned(redditor=f'{post_author}'))
			if submission.created_utc <= last_pass:
				break	

			if ban_check:
				user_banned = True
				banned_date = datetime.fromtimestamp(ban_check.date).strftime('%a, %b %d, %Y at %H:%M:%S')
				ban_note = ban_check.note
			else:
				user_banned = False
				ban_note = None

			if not news_post is None:
				reddit.subreddit(submit_sub).message(
					f"New post in r/{submission.subreddit} referencing r/News.", 
					f"FYI There's a new post in r/{submission.subreddit}.\n\n---\n\nPost Title: [{submission.title}](https://reddit.com{submission.permalink})\n\nPost author: u/{submission.author}\n\nIs post author banned?: {user_banned}\n\nBan note: {ban_note}\n\nOriginal item being linked: {submission.url}"
					)
			
			if not news_title is None: 
				reddit.subreddit(submit_sub).message(
					f"New post in r/{submission.subreddit} referencing r/News.", 
					f"FYI There's a new post in r/{submission.subreddit}.\n\n---\n\nPost Title: [{submission.title}](https://reddit.com{submission.permalink})\n\nPost author: u/{submission.author}\n\nIs post author banned?: {user_banned}\n\nBan note: {ban_note}\n\nOriginal item being linked: {submission.url}"
					)      

	except KeyboardInterrupt:
			print('\nShutting down....')
			sys.exit(1)

	except Exception as e:
		print(f'\t### ERROR - Could not check meta subs for some reason...\n\t{e}')
		traceback.print_exc()



def parse_modmail(subreddit):
	print('Checking modmail notifications...')
	try:
		for conversation in reddit.subreddit(sub_name).modmail.conversations(state='all'):
			archive = None
			#  Comments
			if len(conversation.authors) == 1 and \
					conversation.authors[0].name in {"AutoModerator"} and \
					len(conversation.messages) == 1 and 'comment' in conversation.subject:


				links = re.findall(r'(?:reddit.com/r/\w*/comments/\w*/\w*/)(\w*)', conversation.messages[0].body_markdown)	
				if len(links) == 1:
					comment = reddit.comment(links[0])
					if comment.body == "[deleted]" or comment.author == "[deleted]":
						archive = "Deleted by user"
					if comment.removed:
						banned_time = datetime.fromtimestamp(comment.banned_at_utc).strftime('%a, %b %d, %Y at %H:%M:%S')
						archive = f"Removed by u/{comment.banned_by}.\n\nWhen: {banned_time}"
					if comment.banned_by == 'AutoModerator':
						banned_time = datetime.fromtimestamp(comment.banned_at_utc).strftime('%a, %b %d, %Y at %H:%M:%S')
						archive = f"Removed by u/{comment.banned_by}.\n\nWhen: {banned_time}"
					if comment.locked:
						archive = f"Comment was locked."
					if comment.approved:
						approved_time = datetime.fromtimestamp(comment.approved_at_utc).strftime('%a, %b %d, %Y at %H:%M:%S')
						archive = f"Approved by u/{comment.approved_by}.\n\nWhen: {approved_time}"				
			#  Submissions
			if len(conversation.authors) == 1 and \
					conversation.authors[0].name in {"AutoModerator"} and \
					len(conversation.messages) == 1 and 'submission' in conversation.messages[0].body_markdown:   #conversation.subject:
				links = re.findall(r'(?:reddit.com/r/\w*/comments/)(\w*)', conversation.messages[0].body_markdown)
				if len(links) == 1:
					submission = reddit.submission(links[0])
					if submission.selftext == "[deleted]" or submission.author == "[deleted]":
						archive = "Deleted by user."
					if submission.removed:
						banned_time = datetime.fromtimestamp(submission.banned_at_utc).strftime('%a, %b %d, %Y at %H:%M:%S')
						archive = f"Removed by u/{submission.banned_by}.\n\nWhen: {banned_time}"
					if submission.banned_by == 'AutoModerator':
						banned_time = datetime.fromtimestamp(submission.banned_at_utc).strftime('%a, %b %d, %Y at %H:%M:%S')
						archive = f"Removed by u/{submission.banned_by}.\n\nWhen: {banned_time}"
					if submission.locked:
						archive = f"Submission was locked."
					if submission.approved:
						approved_time = datetime.fromtimestamp(submission.approved_at_utc).strftime('%a, %b %d, %Y at %H:%M:%S')
						archive = f"Approved by u/{submission.approved_by}.\n\nWhen: {approved_time}"
			if archive is not None:
				print(f"Archiving automod notification: {conversation.id}")
				conversation.reply(archive, internal = True)
				conversation.archive()        
	except KeyboardInterrupt:
			print('\nShutting down....')
			sys.exit(1)

	except Exception as e:
		print("\t\n### ERROR - Modmail notifications could not be archived.")
		traceback.print_exc()
	print('Okay, done archiving modmail...')
	#print('====================================')
	print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
	print('Pausing 30 seconds for new mod reports...\n')


##############################
# Bot starts here	

if __name__ == "__main__":

	try:
			# Connect to reddit and return the object
			reddit = reddit_login()

			# Connect to the sub
			subreddit = reddit.subreddit(sub_name)

	except Exception as e:
		print('\t\n### ERROR - Could not connect to reddit.')
		sys.exit(1) 
		
	# Loop the bot
	while True:

		try:

			ban_on_phrase(subreddit)
			micro_conditions(subreddit)
			links_list = report_remove_gather(subreddit)
			report_cleanser(links_list)
			check_mod_log(subreddit)
			parse_modmail(subreddit)

						
		except KeyboardInterrupt:
			print('\nShutting down....')
			sys.exit(1)

		except Exception as e:
			print(f'\t### ERROR - Something went wrong.\n\t{e}')
			sys.exit(1)

		# Loop every X seconds, defined above (currently 30 seconds)
		time.sleep(sleep_seconds) 

