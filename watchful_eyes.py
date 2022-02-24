
# Watchful Eyes Ban Bot v.2 by u/BuckRowdy 

# Import modules
import praw
import pmtw
import time
from time import localtime, timezone
from datetime import datetime as datetime, timedelta as td, date, timezone
import config
import traceback

##################################
# Define Variables

# Define ths sub to work on.  Usernotes will not work accurately on r/mod.  Each sub must be listed individually.
# Sub names are defined in the config file. 
sub_name = config.sub_name

# Number of seconds to sleep between scans
sleep_seconds = 30

# User Defined nickname for ban reasons. Put what you go by on your subs here. 
nick_name = 'Bucky'

# Define your ban notes here.  These are for the ban note in the upper right corner of modmail in red.
# Both fields are editable, but you must use the letters in the first column in your report reason.
# Report reasons always start with 'ban' followed by the time then the code for the reason.  
# A 30 day ban for trolling would read as follows: ban 30 t
# Permanent bans are input as 0.  So a perm ba for covid misinfo would be ban 0 c

ban_macros = 		{ 	'c' : 'Covid Misinfo',
				'v' : 'Violent Content',
				'r' : 'Racism',
				't' : 'Trolling',
				's' : 'Spam',
				'm' : 'Misinformation'
			}



###  Defines the reddit login function
#    A refresh token is used so you can maintain 2FA on the bot account.
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


### Process ModQueue comments 
#   Comments and Submissions are processed separately.
def check_comments(subreddit):
	try: 
		ban_phrase = 'ban'
		# Prints the ban syntax to the terminal so you can easily reference.
		print('\nBan syntax:\nban <days> [macro]\n<0> days for perm\n\nMacros:\n[c] Covid\n[v] Violence\n[s] Spam\n[r] Racism\n[t] Trolling\n[m] Misinfo\n\n')
		for item in subreddit.mod.modqueue(limit=None):
			# T1 is reddit's code for comment objects.
			if item.fullname.startswith("t1_") and len(item.mod_reports):
				
				# Ban message field has a 1000 character limit so quoted comments need to be sliced to prevent api errors.
				comment_slice = f'{item.body}'
				sliced_comment = comment_slice[:300]
				item_type = 'Comment'
				
				# Set up a ban header, footer, and comment quote.  Gives granular control over these fields.
				ban_header = f'This **{item_type}** may have fully or partially contributed to your ban:\n\n'
				ban_footer = f'**[^(Context)]({item.permalink}?context=9)** ¯¯ **[^(r/{item.subreddit} rules)](http://www.reddit.com/r/{item.subreddit}/about/rules)** ¯¯ **[^(Reddit Content Policy)](https://www.redditinc.com/policies/content-policy)**\n\n'
				comment_quote = f'\n> [{sliced_comment}...]({item.permalink})\n\n'

				# Go through the mod reports and parse the info for ban details.
				for report_reason, mod_name in item.mod_reports:
					if ban_phrase in report_reason:
						items = report_reason.split(" ")
						ban_duration = items[1]
						ban_reason = items[2]
						ban_length = int(ban_duration)
						
						# Ban note is a field in the /about/banned page as well as in modmail and modlog. 
						# Here, the ban note is taken from a user defined dictionary. 
						ban_note = ban_macros[ban_reason]
						print('Mod report found...')
						time.sleep(1)
						print(f'r/{item.subreddit} | {mod_name}: {report_reason}')
						 
						if len(items) > 1:
							if items[0] == 'ban':
								item.mod.remove()
								item.mod.lock()
								print(f"REMOVE ITEM {item.fullname}")
								ban_sub = item.subreddit.display_name

								# Ban length of 0 for permanent bans, any other digit will trigger a temp ban.
								if ban_length == 0:
									if ban_reason in ban_macros:
										ban_note = ban_macros[ban_reason]
										ban_message = '**'+ban_note+'**\n\n'+ban_header+comment_quote+ban_footer
										reddit.subreddit(ban_sub).banned.add(
															f'{item.author}', 
															ban_reason=f'{ban_note} - {nick_name}', 
															ban_message=f'{ban_message}', 
															note=f'{item.permalink}'
															)										
										
										print(f"{mod_name} banned {item.author} permanently.")

										# Create and post a usernotes object for this item.
										notes = pmtw.Usernotes(reddit, item.subreddit)
										n = pmtw.Note(
														user=f'{item.author}', 
														note=f'ban - {ban_note}',
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
															ban_reason=f'{ban_note} - {nick_name}', 
															duration=ban_length, 
															ban_message=f'{ban_message}', 
															note=f'{item.permalink}'
															)

										print(f"{mod_name} banned {item.author} for {ban_duration} days.")
										notes = pmtw.Usernotes(reddit, item.subreddit)
										n = pmtw.Note(
														user=f'{item.author}', 
														note=f'{ban_length}d - {ban_note}',
														link=f'{item.permalink}',
														warning='ban'
														)
										notes.add_note(n)
										
								break
	except Exception as e:
			print('\t### ERROR - Something went wrong processing comments.')
			print(e)
			traceback.print_exc()						
										

def check_submissions(subreddit):
	try: 
		ban_phrase = 'ban'
		for item in subreddit.mod.modqueue(limit=None):
			if item.fullname.startswith("t3_") and len(item.mod_reports):
				notes = pmtw.Usernotes(reddit, item.subreddit)
				item_type = 'Submission'
				ban_header = f'This **{item_type}** may have fully or partially contributed to your ban:\n\n'
				ban_footer = f'**[^(Context)]({item.permalink}?context=9)** ¯¯ **[^(r/{item.subreddit} rules)](http://www.reddit.com/r/{item.subreddit}/about/rules)** ¯¯ **[^(Reddit Content Policy)](https://www.redditinc.com/policies/content-policy)**\n\n'
				post_quote = f'\n> [{item.title}]({item.url})\n\n---\n\n'

				for report_reason, mod_name in item.mod_reports:
					if ban_phrase in report_reason:
						items = report_reason.split(" ")
						ban_duration = items[1]
						ban_reason = items[2]
						ban_length = int(ban_duration)
						ban_note = ban_macros[ban_reason]
						print('Mod report found...')
						time.sleep(1)
						print(f'r/{item.subreddit} | {mod_name}: {report_reason}')
						time.sleep(1) 
		
						if len(items) > 1:
							if items[0] == 'ban':
								item.mod.remove()
								item.mod.lock()
								print(f"REMOVE ITEM {item.fullname}")
								ban_sub = item.subreddit.display_name								

								if ban_length == 0:
									if ban_reason in ban_macros:
										ban_note = ban_macros[ban_reason]
										ban_message = '**'+ban_note+'**\n\n'+ban_header+post_quote+ban_footer
										reddit.subreddit(ban_sub).banned.add(
															f'{item.author}', 
															ban_reason=f'{ban_note} - {nick_name}', 
															ban_message=f'{ban_message}', 
															note=f'{item.permalink}'
															)
										
										print(f"{mod_name} banned {item.author} permanently.")
										notes = pmtw.Usernotes(reddit, item.subreddit)
										n = pmtw.Note(
												user=f'{item.author}', 
												note=f'ban - {ban_note}',
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
															ban_reason=f'{ban_note} - {nick_name}', 
															duration=ban_length, 
															ban_message=f'{ban_message}', 
															note=f'{item.permalink}'
															)
										
										print(f"{mod_name} banned {item.author} for {ban_duration} days.")
										notes = pmtw.Usernotes(reddit, item.subreddit)
										n = pmtw.Note(
														user=f'{item.author}', 
														note=f'ban - {ban_note}',
														link=f'{item.permalink}',
														warning='ban'
														)
										notes.add_note(n)
										
								break
	except Exception as e:
			print('\t### ERROR - Something went wrong processing submissions.')
			print(e)
			traceback.print_exc()

##############################
# Bot starts here				

if __name__ == "__main__":

	try:
			# Connect to reddit and return the object
			reddit = reddit_login()

			# Connect to the sub(s)
			subreddit = reddit.subreddit(sub_name)

	except Exception as e:
		print('\t\n### ERROR - Could not connect to reddit.')
		sys.exit(1) 
		
	while True:

		try:	
			ban_comments = check_comments(subreddit)
			ban_posts = check_submissions(subreddit)
							
		except Exception as e:
			print('\t### ERROR - Something went wrong.')
			print(e)
			traceback.print_exc()

		# Loop every X seconds, defined above (1 minute, currently.)
		time.sleep(sleep_seconds) 



