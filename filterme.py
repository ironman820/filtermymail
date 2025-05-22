from email.header import decode_header
from imapclient import IMAPClient, exceptions

import atexit
import dotenv
import email
import os
import pandas as pd
import pyzmail


def email_to_pandas(client: IMAPClient, folder: str = "INBOX") -> pd.DataFrame:
    client.select_folder(folder, True)
    uids: list = client.search()
    raw_messages: dict[int, dict] = client.fetch(uids, data=["BODY[]"])
    emails: pd.DataFrame = pd.DataFrame.from_dict(raw_messages, "index")
    # emails["uid"] = emails[0]
    # emails.drop([0], axis="columns", inplace=True)
    # for uid in uids:
    #     message: pyzmail.PyzMessage = pyzmail.PyzMessage.factory(
    #         raw_messages[uid][b"BODY[]"]
    #     )
    #     print(message.get_subject())
    #     break
    emails = emails.drop(emails.iloc[:, :1].columns.to_list(), axis="columns")
    emails = emails.reset_index()
    emails.columns = ["uid", "message"]
    emails[["subject", "from"]] = emails["message"].apply(
        lambda x: pd.Series(breakout_email_columns(x), index=["subject", "from"])
    )
    return emails


def breakout_email_columns(raw_message) -> list:
    # message: pyzmail.PyzMessage = pyzmail.PyzMessage.factory(raw_message)
    message = email.message_from_bytes(raw_message)
    subject = decode_header(message["subject"])[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode()
    return [subject, message.get("From")]


def final_logout(client: IMAPClient) -> None:
    print("Application finished, logging out.")
    client.logout()


def login(hostname: str, user: str, password: str, use_ssl: bool = True) -> IMAPClient:
    imap_object = IMAPClient(hostname, ssl=use_ssl)
    try:
        imap_object.login(user, password)
    except exceptions.LoginError:
        print("Could not log into mail server")
        exit()
    atexit.register(final_logout, imap_object)
    return imap_object


def logout(client: IMAPClient):
    client.logout()
    atexit.unregister(final_logout)


def main_process() -> None:
    dotenv.load_dotenv("settings.env")
    client: IMAPClient = login(
        os.getenv("email_host", "badhost"),
        os.getenv("email_user", "user"),
        os.getenv("email_password", "badpass"),
        False,
    )
    emails: pd.DataFrame = email_to_pandas(client)
    print(emails)
    print(emails["subject"])


if __name__ == "__main__":
    main_process()
