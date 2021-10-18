import logging
from typing import Dict

from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

from twilio.rest import Client

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ['Nome'],
    ['CPF', 'RG'],
    ['Numero'],
    ['Tipo de especialidade'],
    ['Enviar'],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Função auxiliar para formatar as informações coletadas do usuário."""
    facts = [f'{key} - {value}' for key, value in user_data.items()]
    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, context: CallbackContext) -> int:
    """Inicie a conversa e peça informações ao usuário."""
    update.message.reply_text(
        "Olá! Sou seu bot de atendimento. Precisamos de algumas infomações para marcar sua consulta: ",
        reply_markup=markup,
    )

    return CHOOSING


def regular_choice(update: Update, context: CallbackContext) -> int:
    """Peça ao usuário informações sobre a escolha predefinida selecionada."""
    text = update.message.text
    context.user_data['choice'] = text
    if(text.lower() == "numero"):
        update.message.reply_text(f'Você escolheu {text.lower()}.\nInforme seguindo o padrão Internacional:\nEx:(+55929XXXXXXXX)\n')
    else:
        update.message.reply_text(f'Você escolheu {text.lower()}.\nInforme:')

    return TYPING_REPLY


def received_information(update: Update, context: CallbackContext) -> int:
    """Armazene informações fornecidas pelo usuário e solicite a próxima categoria."""
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text(
        "Suas informações:"
        f"\n{facts_to_str(user_data)}\nResponda a todas às informações.\n"
        "Você pode corrigir os dados clicando novamente.\n",
        reply_markup=markup,
    )

    return CHOOSING


def done(update: Update, context: CallbackContext) -> int:
    """Exiba as informações coletadas e encerre a conversa."""
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text(
        f"Suas informações:\n{facts_to_str(user_data)}\nSua consulta foi marcada!\n\n[IMPORTANTE]\nVamos avaliar seus dados, \nAguarde confirmação por SMS.",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    if(user_data.get("Numero")!=None):
        """chaves do sms"""
        account_sid = "AC738ef6ed068b6a53304d47a87cb133c2"
        auth_token = "7452730d9a49d1fc9634fd71b9ca7921"
        client = Client(account_sid,auth_token)
        client.messages.create(from_="+18454787737",body="Sua consulta foi marcada com Sucesso.",to=user_data.get("Numero"))

    user_data.clear()
    return ConversationHandler.END


def main() -> None:
    
    """Run the bot."""
    # Crie o Updater e passe a ele o token do seu bot.
    updater = Updater("2012994382:AAG22TgNT6jiPHfl6lfMmpIGmLc7xstnVPQ")

    # Faça com que o despachante registre manipuladores
    dispatcher = updater.dispatcher

    # Adicione o gerenciador de conversas com os estados CHOOSING, TYPING_CHOICE e TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.regex('^(Nome|CPF|RG|Numero|Tipo de especialidade)$'), regular_choice
                ),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Enviar$')), regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Enviar$')),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Enviar$'), done)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()
    
    updater.idle()


if __name__ == '__main__':
    main()
