import PyPDF2


def get_fullname(client, ident):
    """
    :param client: OpenReview client
    :param ident: OpenReview Profile ID
    :return: str, The full name of an OpenReview Profile
    """
    names = client.get_profile(ident).content['names'][0]
    return names['fullname']


def send_email(client, recipients, title, message):
    """
    :param client: OpenReview Client object
    :param recipients: the list of emails or IDs
    :param title: title of the email
    :param message: text message to be sent
    :return: None
    """
    closing = f"""\n\nBest regards,\nNegar Kiyavash, Joris Mooij\nUAI 2024 Program Chairs"""
    for r in recipients:
        opening = f"""Dear {get_fullname(client, r)},\n\n"""
        text = opening + message + closing
        client.post_message(
            subject=title,
            recipients=[r],
            replyTo='uai2024chairs@gmail.com',
            message=text
        )
    return None


def find_word_in_pdf(pdf_path, target_word):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        for page_number in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_number]
            text = page.extract_text()

            if target_word.lower() in text.lower():
                # Find the position of the target word
                start_index = text.lower().find(target_word.lower())
                # Extract text before the target word
                text_before = text[:start_index].strip()
                return page_number + 1, text_before  # Page numbers start from 1

    return None, None


