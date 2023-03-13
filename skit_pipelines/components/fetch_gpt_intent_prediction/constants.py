INTENT_MODEL: str = "text-davinci-003"
ALLOWED_INTENTS = ['_confirm_', '_cancel_']

PROMPT_TEXT = """In the below conversation turn between a debt collection bot and a user:

STATE: {{state}}
{{conversation_context}}

If the user is answering the bot with an affirmative or confirming what the bot says (consider yep, yeah, or the like as "yes"), answer ‘_confirm_’
If the user is denying what the bot says, answer ‘_cancel_’
If the user is unsure, answer '_maybe_'
If the user asks who the bot is, where the bot is calling from, or why the bot is calling, answer ‘_identity_’
If the user requests that the bot repeat something, answer ‘_repeat_’
If the user doesn't wish to speak to machines and robots or wants to speak to a human agent / operator / customer service / person, answer 'ask_for_agent'
If the user is greeting the bot or saying hello, answer ‘_greeting_’
If the user appears to be providing a 4 digit number when the bot asks for their social security number, answer 'inform_ssn_number'
If the user appears to be providing a date when the bot asks for their date of birth , answer 'inform_dob'
If the user is saying anything else or you are unsure of what they are saying, answer ‘Other’

Answer:"""