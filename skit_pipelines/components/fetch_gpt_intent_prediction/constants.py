INTENT_MODEL: str = "text-davinci-003"
ALLOWED_INTENTS = ["_confirm_", "_cancel_"]


def get_prompt_text():
    return """In the below conversation turn between a debt collection bot and a user:

STATE: COF
[Bot]: <speak><prosody rate="102%">Hello. Am I speaking with stephanie brown-stewart?</prosody></speak> \n [User]: yes

Answer "_confirm_" if the user is confirming;
Answer "_cancel_" if the user is denying;
Answer "Other" if the user says anything else.

Answer: _confirm_

In the below conversation turn between a debt collection bot and a user:

{{state}}
{{conversation_context}}

Answer "_confirm_" if the user is giving the bot a positive response or confirming what the bot says (yep, yeah, or similar expressions are taken to mean "yes");
Answer "_cancel_" if the user is refuting what the bot says;
Answer "_maybe_" if the user is undecided or provides an ambiguous response, such as possibly;
Answer "_identity_" if the user asks who the bot is, where it is calling from, or why it is calling;
Answer "other_language" if the user appears to not speak English, does not feel at ease speaking English, or requests that we speak to them in an other language, such as Spanish;
Answer "_greeting_" if the user is greeting the bot or saying hello;
Answer "ask_for_agent" if the user prefers to communicate with a human agent or operator rather than a machine or robot;
Answer "wrong_number" if the user says that the bot called the wrong number or the wrong person;
Answer "_repeat_" if the user asks the bot to repeat something;
Answer "_what_" if the user looks to be having problems understanding the bot or if they are asking a question;
Answer "dispute_debt" if it appears that the user is disputing the debt or insisting they owe nothing;
Answer "cease_desit" if the user requests that we stop calling them, remove them from our call list, stop bothering them, or threatens to sue us;
Answer 'put_on_hold' if it looks that the user is asking the bot to wait or hold for a moment;
Answer "inform_phone_number" if the user appears to be providing a number when the bot asks for their mobile number;
Answer 'wont_pay' if the user refuses to pay or if they are unwilling to make a payment;
Answer "inform_fund_shortage" if it appears that the user is attempting to indicate that they are currently short on funds or have recently made a significant expenditure;
Answer "ask_for_installment" if the user mentions a figure that is less than the amount owed or indicates they would like to pay in smaller amounts;
Answer "_callback_" if the user later requests a callback from the bot;
Answer "inform_pay_later" if it appears that the user intends to pay later;
Answer "date_entity_only" if it appears that the user is providing a date;
Answer "inform already paid" if the user appears to have already made a payment;
Answer "Other" if the user says anything else or if you are unsure of what they are saying.

Answer:"""
