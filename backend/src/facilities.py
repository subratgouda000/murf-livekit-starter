FACILITIES = {
    "bhubaneswar": {"name": "Capital Hospital", "type": "Government Hospital", "address": "Unit 6, Bhubaneswar, Odisha"},
    "cuttack": {"name": "SCB Medical College and Hospital", "type": "Government Hospital", "address": "Mangalabag, Cuttack, Odisha"},
    "delhi": {"name": "AIIMS Delhi", "type": "Government Hospital", "address": "Ansari Nagar, New Delhi"},
    "mumbai": {"name": "KEM Hospital", "type": "Government Hospital", "address": "Parel, Mumbai, Maharashtra"},
    "bangalore": {"name": "Victoria Hospital", "type": "Government Hospital", "address": "Fort, Bangalore, Karnataka"},
    "chennai": {"name": "Government General Hospital", "type": "Government Hospital", "address": "Park Town, Chennai, Tamil Nadu"},
    "kolkata": {"name": "SSKM Hospital", "type": "Government Hospital", "address": "Bhowanipore, Kolkata, West Bengal"},
    "hyderabad": {"name": "Osmania General Hospital", "type": "Government Hospital", "address": "Afzal Gunj, Hyderabad, Telangana"},
    "pune": {"name": "Sassoon General Hospital", "type": "Government Hospital", "address": "Near Pune Station, Pune, Maharashtra"},
    "lucknow": {"name": "King George Medical University", "type": "Government Hospital", "address": "Chowk, Lucknow, Uttar Pradesh"},
}


def lookup_facility(district: str):
    key = district.strip().lower()
    return FACILITIES.get(key)
