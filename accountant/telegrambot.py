import logging
from io import BytesIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import *
from django_telegrambot.apps import DjangoTelegramBot
from moneyed import Money
from telegram import Update, Bot
from telegram.ext import CommandHandler, MessageHandler, Filters

from accountant.misc.fns_parser import is_valid_invoice, parse
from accountant.models import Account, Document

logger = logging.getLogger(__name__)

IN_MEMORY_LIMIT = int(2.5 * 2 ** 20)  # 2.5 megabytes


def start(bot, update):
    user = User.objects.filter(
        telegram_username__username=update.message.from_user.username
    ).first()
    if user is not None:
        bot.sendMessage(
            update.message.chat_id,
            "Hi, {}!".format(user.first_name)
        )
    else:
        bot.send_message(
            update.message.chat_id,
            ('You are not registered as authorized user. Please visit your '
             'admin panel and fix it')
        )


def json_handler(bot: Bot, user: User, document: Document, update: Update):
        default_expense = getattr(settings, 'DEFAULT_EXPENSE', 10)
        default_account = getattr(settings, 'DEFAULT_ACCOUNT', 2)

        result = parse(
            document.file.read().decode(),
            user,
            Account.objects.get(pk=default_expense),
            Account.objects.get(pk=default_account)
        )
        bot.send_message(
            update.message.chat_id,
            "Invoice parsed successfully. {} items, total sum {}"
            .format(
                result.transactions.count() - 1,
                Money(-result.pnl[0]['amount'], result.pnl[0]['currency'])
            )
        )


def document_handler(bot: Bot, update: Update):
    user = User.objects.filter(
        telegram_username__username=update.message.from_user.username
    ).first()
    if user is not None:
        logger.debug('User identified as {}'.format(user))
        if update.message.document is not None:
            remote_file = bot.getFile(update.message.document.file_id)
            if remote_file.file_size < IN_MEMORY_LIMIT:
                local_file = InMemoryUploadedFile(
                    file=BytesIO(),
                    field_name=None,
                    name=update.message.document.file_name,
                    content_type=update.message.document.mime_type,
                    size=remote_file.file_size,
                    charset=None
                )
            else:
                local_file = TemporaryUploadedFile(
                    name=update.message.document.file_name,
                    content_type=update.message.document.mime_type,
                    size=remote_file.file_size,
                    charset=None
                )
            remote_file.download(out=local_file)
            logger.info('File {} downloaded via Telegram API'.format(local_file))

            document = Document.objects.create(
                file=local_file,
                invoice=None,
                description=''
            )

            local_file.seek(0)
            if is_valid_invoice(local_file.read().decode()):
                json_handler(bot, user, document, update)
            else:
                bot.send_message(
                    update.message.chat_id,
                    'Attached document has been saved as {} ({})'
                    .format(document, document.file.url)
                )
    else:
        bot.send_message(
            update.message.chat_id,
            ('You are not registered as authorized user. Please visit your '
             'admin panel and fix it')
        )


def main():
    dispatcher = DjangoTelegramBot.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.document, document_handler))
