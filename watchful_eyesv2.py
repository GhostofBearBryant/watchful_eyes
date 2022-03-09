
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
sub_name = 'marchagainstnazis+news+politicalhumor+questions+ask+kitchenconfidential+chattanooga+unresolvedmysteries'


# Number of seconds to sleep between scans
sleep_seconds = 30

# Sub to log bans and admin actions.  Admin removals and bans by this account will be logged in the sub.
submit_sub = "submanagerbot"


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
							'cs': 'Comment Spam'
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
	print(f'Logged in as: {reddit.user.me()}')
	return reddit


# Process ModQueue comments and submissions for the ban phrase.

def ban_on_phrase(subreddit):
	try: 
		ban_phrase = 'ban'
		###  Process Comments
		# Prints the ban syntax to the terminal so you can easily reference.
		print('\nBan syntax:\nban <days> [macro]\n<0> days for perm\n\nReport reasons:\n[c] Covid\n[cs] Comment Spam\n[v] Violence\n[s] Spam\n[r] Racism/Bigotry\n[t] Trolling\n[m] Misinformation\n[d] Dehumanizing speech\n[n] Nazi\n[b] Brigading\n[h] Hate Speech\n\n')
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
										
								
	except Exception as e:
			print(f'\t### ERROR - Something went wrong processing the modqueue.\n\t{e}')
			traceback.print_exc()					
	

#  This functions logs bans and admin level actions to a private log sub.  The list of monitored subs is smaller because other bots are logging for other subs.
def check_mod_log(subreddit):
	now = time.time()
	last_pass = (now  - 45)
		
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

		for log in reddit.subreddit('news+politicalhumor+marchagainstnazis').mod.log(limit = None):
			if log.created_utc <= last_pass:
				break

			if log.action == 'banuser':
			#if log.action == 'banuser' and log.subreddit == 'news':
				log_description = log.description.rsplit(' ',1)
				ban_reason_raw = log.description.split('-',1)
				ban_reason = ban_reason_raw[0]
				description = log_description[1]
				date_stamp = datetime.fromtimestamp(int(log.created_utc)).strftime('%m/%d/%y')
				log_post_selftext = f"Sub: r/{log.subreddit}\n\nAction: {log.action}\n\nMod: {log.mod}\n\nWhen: {time_stamp}\n\n---\n\nTitle: {log.target_title}\n\nTarget Author: u/{log.target_author}\n\nBody: {log.target_body}\n\nDetails: {log.details}\n\nLog Description: {log.description}\n\nPermalink: {description}\n\n[*Subreddit modlog*](http://reddit.com/r/{log.subreddit}/about/log)\n\n" #^(Links to ban items are not functional, view mod log instead.)"
				log_post_title = f"User u/{log.target_author} banned by u/{log.mod} in r/{log.subreddit} on {date_stamp}. Note: {ban_reason}"
				reddit.subreddit(submit_sub).submit(log_post_title, log_post_selftext)
				print(f"Action: >{log.action}< in r/{log.subreddit} was posted in r/submanagerbot.")
			else:
				continue
					        
	except Exception as e:
		print(f'\t### ERROR - Could not process mod log.\n\t{e}')



# Check the mod log for threads removed in the past day and log their fullnames for removing reported comments. 
def report_remove_gather(subreddit):
	links_list = []
	# Saves a copy as a text file in case it needs to be referenced. 
	with open("/home/pi/bots/news/links_list.txt", "w+") as f:
		print("gathering links....")
		now = time.time()
		last_pass = (now - 60*60*24)
		for log_item in reddit.subreddit(sub_name).mod.log(limit = None):
			if log_item.created_utc >= last_pass:			
				if log_item.action == 'removelink':
					if log_item.mod != 'AutoModerator':						
						logged_item = log_item.target_fullname
						if logged_item not in links_list:
							links_list.append(str(logged_item))							
		f.write(f"{links_list}")	
		return links_list				
	f.close()
	print("Done gathering..")


# Check for reported comments in removed threads and remove them. 
def report_cleanser(links_list):
	print("Working on links....")
	if len(links_list) > 0:
			print('Ok. Checking reports on removed posts...')
			for item in reddit.subreddit(sub_name).mod.reports(limit = None):
				if item.fullname.startswith("t1_"):
					if item.link_id in links_list:
						item.mod.remove()
						print(f'REMOVE ITEM: r/{item.subreddit} {item.permalink}')
	else:
		print('None found')
	print("Finished removing any reported comments in removed threads....")
	print('====================================')
	print('Awaiting mod reports...')

			
## This function checks the modqueue and implements various custom micro conditions to reduce workload.
def custom_micro_conditions(subreddit):
	try:
		for item in reddit.subreddit(sub_name).mod.reports(limit = None):
			
			#  Approve any reported comments by automoderator. 
			if item.author_fullname == 't2_6l4z3':
				item.mod.approve()
				print('Approved AutoMod comment')
			
			# This check removes reported comments with 'tard' phrases in them.
			if item.fullname.startswith("t1_"):
				report_body = item.body
				ableism_search = re.search(r'(?i)(fuck|trump|vaxx|lib|re|conserva)tards?', report_body)
				if not ableism_search is None:
					item.mod.remove()
					print(f"REMOVE ITEM {item.fullname}  {item.permalink}")

	except Exception as e:
		print('\t\n### ERROR - Could not approve automod')
		traceback.print_exc()


##############################
# Bot mechanism starts here	

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

			ban_comments = ban_on_phrase(subreddit)
			check_log = check_mod_log(subreddit)
			approve_comments = custom_microconditions(subreddit)
			links_list = report_remove_gather(subreddit)
			check_reports = report_cleanser(links_list)
			
						
		except KeyboardInterrupt:
			print('Shutting down....')
			sys.exit(1)

		except Exception as e:
			print(f'\t### ERROR - Something went wrong.\n\t{e}')
			sys.exit(1)

		# Loop every X seconds, defined above (currently 30 seconds)
		time.sleep(sleep_seconds) 



