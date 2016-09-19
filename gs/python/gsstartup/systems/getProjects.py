#!/usr/bin/env python

import os
import argparse
import pprint
import smtplib

projectRoot = '/scholar/projects'
excludeFolders = ['.hell', '.purgatory', '.restores', '.restores', '.TemporaryItems', '_duplicatejob', '_temp', '.snapshot', 'MUSTACHE2', ]
defaultRecipients = ['producers@gentscholar.com', 'will@gentscholar.com', 'sysadmin@gentscholar.com']

def main():
    for p in sorted(getProjects(), key=str.lower):
        print p

def email(recipients):
    if not recipients:
        recipients = defaultRecipients
    fromaddr = 'anthony@gentscholar.com'
    toaddr = ",".join(recipients)
    msg = "\r\n".join([
        "From: %s" %fromaddr,
        "To: %s" %toaddr,
        "Subject: Server cleanup",
        "",
        "Yo!",
        "",
        "Here's a list of open projects on the server. Please let me know what I can archive. kthxbaixoxo143",
        ""
        ]+sorted(getProjects(), key=str.lower))

    server = smtplib.SMTP('localhost')
    server.ehlo()
    server.sendmail(fromaddr, recipients, msg)
    server.quit()


def getProjects():
    folders = [x for x in os.listdir(projectRoot) if os.path.isdir(os.path.join(projectRoot, x))]
    projects = list(set(folders) - set(excludeFolders))
    return projects

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prints all active projects on server. Optionally, e-mail producers@gentscholar.com alias asking what is ok to archive.')
    parser.add_argument('-e', '--email', action='store_true', help='Send e-mail to producers@gentscholar.com asking what projects can be archived. If -r supplied as well, will e-mail specified recipients.')
    parser.add_argument('-r', '--recipients', nargs='*', help='List of recipients.')

    args = parser.parse_args()

    if args.email:
        email(args.recipients)
    else:
        main()
