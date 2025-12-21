"""
Application parameters configuration.
Customize these values to control MailMind behavior.
"""

import os

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                           EMAIL PARAMETERS                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

# Maximum number of emails to fetch from inbox per run
EMAIL_COUNT = 10

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                           CONTENT PARAMETERS                               ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

# Maximum characters to show in email body preview
BODY_PREVIEW_LENGTH = 500

# Maximum characters of email body sent to LLM for classification
LLM_BODY_LIMIT = 1500
