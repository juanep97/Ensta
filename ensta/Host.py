import requests
import requests.cookies
from json import JSONDecodeError
import random
import string
from .Guest import Guest
from .lib.Commons import (
    refresh_csrf_token,
    update_app_id,
    update_homepage_source,
    update_session
)
from .lib import (
    AuthenticationError,
    NetworkError
)


class Host:
    request_session: requests.Session = None
    homepage_source: str = None
    insta_app_id: str = None
    preferred_color_scheme: str = "dark"
    x_ig_www_claim: str = None
    csrf_token: str = None
    guest: Guest = None

    def __init__(self, session_id: str):
        self.x_ig_www_claim = "hmac." + "".join(random.choices(string.ascii_letters + string.digits + "_-", k=48))
        update_session(self)
        update_homepage_source(self)
        update_app_id(self)
        self.guest = Guest()

        self.request_session.cookies.set("sessionid", session_id)

        if not self.is_authenticated():
            raise AuthenticationError("Either User ID or Session ID is not valid.")

    def update_homepage_source(self):
        temp_homepage_source = requests.get("https://www.instagram.com/").text.strip()

        if temp_homepage_source != "":
            self.homepage_source = temp_homepage_source
        else:
            raise NetworkError("Couldn't load instagram homepage.")

    def is_authenticated(self):
        refresh_csrf_token(self)
        request_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-prefers-color-scheme": self.preferred_color_scheme,
            "sec-ch-ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Google Chrome\";v=\"114\"",
            "sec-ch-ua-full-version-list": "\"Not.A/Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"114.0.5735.91\", \"Google Chrome\";v=\"114.0.5735.91\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"15.0.0\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "viewport-width": "1475",
            "x-asbd-id": "198387",
            "x-csrftoken": self.csrf_token,
            "x-ig-app-id": self.insta_app_id,
            "x-ig-www-claim": self.x_ig_www_claim,
            "x-requested-with": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/edit/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        http_response = self.request_session.get("https://www.instagram.com/api/v1/accounts/edit/web_form_data/", headers=request_headers)

        try:
            http_response.json()
            return True
        except JSONDecodeError:
            return False

    def follow_user_id(self, user_id: str | int):
        user_id = str(user_id).strip()
        refresh_csrf_token(self)
        random_referer_username = "".join(random.choices(string.ascii_lowercase, k=6))
        body_json = {
            "container_module": "profile",
            "nav_chain": f"PolarisProfileRoot:profilePage:1:via_cold_start",
            "user_id": user_id
        }
        request_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded",
            "sec-ch-prefers-color-scheme": self.preferred_color_scheme,
            "sec-ch-ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Google Chrome\";v=\"114\"",
            "sec-ch-ua-full-version-list": "\"Not.A/Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"114.0.5735.91\", \"Google Chrome\";v=\"114.0.5735.91\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"15.0.0\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "viewport-width": "1475",
            "x-asbd-id": "198387",
            "x-csrftoken": self.csrf_token,
            "x-ig-app-id": self.insta_app_id,
            "x-ig-www-claim": self.x_ig_www_claim,
            "x-instagram-ajax": "1007616494",
            "x-requested-with": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/{random_referer_username}/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

        failure_response = {"success": False, "following": None, "follow_requested": None, "previous_following": None, "is_my_follower": None}
        http_response = self.request_session.post(f"https://www.instagram.com/api/v1/friendships/create/{user_id}/", headers=request_headers, data=body_json)

        try:
            response_json = http_response.json()

            if "status" in response_json:
                if response_json["status"] == "ok" and "friendship_status" in response_json:
                    if "following" in response_json["friendship_status"] \
                            and "outgoing_request" in response_json["friendship_status"] \
                            and "followed_by" in response_json["friendship_status"] \
                            and "previous_following" in response_json:
                        return {
                            "success": True,
                            "following": response_json["friendship_status"]["following"],
                            "follow_requested": response_json["friendship_status"]["outgoing_request"],
                            "is_my_follower": response_json["friendship_status"]["followed_by"],
                            "previous_following": response_json["previous_following"]
                        }
                    else: return failure_response
                else: return failure_response
            else: return failure_response
        except JSONDecodeError: return failure_response

    def follow_username(self, username: str):
        username = username.lower().strip().replace(" ", "")
        user_id_response = self.guest.get_userid(username)
        failure_response = {"success": False, "following": None, "follow_requested": None, "previous_following": None, "is_my_follower": None}

        if user_id_response["success"]:
            return self.follow_user_id(user_id_response["user_id"])
        else:
            return failure_response

    def unfollow_user_id(self, user_id: str | int):
        user_id = str(user_id).strip()
        refresh_csrf_token(self)
        random_referer_username = "".join(random.choices(string.ascii_lowercase, k=6))
        body_json = {
            "container_module": "profile",
            "nav_chain": f"PolarisProfileRoot:profilePage:1:via_cold_start",
            "user_id": user_id
        }
        request_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded",
            "sec-ch-prefers-color-scheme": self.preferred_color_scheme,
            "sec-ch-ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Google Chrome\";v=\"114\"",
            "sec-ch-ua-full-version-list": "\"Not.A/Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"114.0.5735.91\", \"Google Chrome\";v=\"114.0.5735.91\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"15.0.0\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "viewport-width": "1475",
            "x-asbd-id": "198387",
            "x-csrftoken": self.csrf_token,
            "x-ig-app-id": self.insta_app_id,
            "x-ig-www-claim": self.x_ig_www_claim,
            "x-instagram-ajax": "1007616494",
            "x-requested-with": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/{random_referer_username}/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

        failure_response = {"success": False, "unfollowed": None}
        http_response = self.request_session.post(f"https://www.instagram.com/api/v1/friendships/destroy/{user_id}/", headers=request_headers, data=body_json)

        try:
            response_json = http_response.json()

            if "status" in response_json:
                if response_json["status"] == "ok" and "friendship_status" in response_json:
                    if "following" in response_json["friendship_status"] \
                            and "outgoing_request" in response_json["friendship_status"]:
                        return {
                            "success": True,
                            "unfollowed": not response_json["friendship_status"]["following"] and not response_json["friendship_status"]["outgoing_request"]
                        }
                    else: return failure_response
                else: return failure_response
            else: return failure_response
        except JSONDecodeError: return failure_response

    def unfollow_username(self, username: str):
        username = username.lower().strip().replace(" ", "")
        user_id_response = self.guest.get_userid(username)
        failure_response = {"success": False, "unfollowed": None}

        if user_id_response["success"]:
            return self.unfollow_user_id(user_id_response["user_id"])
        else:
            return failure_response

    def follower_list_by_userid(self, user_id: str | int, count: int):
        user_id = str(user_id).strip()
        refresh_csrf_token(self)
        random_referer_username = "".join(random.choices(string.ascii_lowercase, k=6))
        request_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-prefers-color-scheme": self.preferred_color_scheme,
            "sec-ch-ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Google Chrome\";v=\"114\"",
            "sec-ch-ua-full-version-list": "\"Not.A/Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"114.0.5735.91\", \"Google Chrome\";v=\"114.0.5735.91\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"15.0.0\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "viewport-width": "1475",
            "x-asbd-id": "198387",
            "x-csrftoken": self.csrf_token,
            "x-ig-app-id": self.insta_app_id,
            "x-ig-www-claim": self.x_ig_www_claim,
            "x-requested-with": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/{random_referer_username}/followers/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

        failure_response = {"success": False, "follower_list": None, "list_size": None}
        max_id = ""
        required_list = []

        while True:
            if max_id != "":
                max_id_text = f"&max_id={max_id}"
            else:
                max_id_text = ""

            http_response = self.request_session.get(f"https://www.instagram.com/api/v1/friendships/{user_id}/followers/?count={30}{max_id_text}&search_surface=follow_list_page", headers=request_headers)

            try:
                response_json = http_response.json()

                if "status" not in response_json or "users" not in response_json:
                    return failure_response

                if response_json["status"] != "ok":
                    return failure_response

                for each_item in response_json["users"]:
                    if len(required_list) < count or count == 0:
                        required_list.append(each_item)

                if (len(required_list) < count or count == 0) and "next_max_id" in response_json:
                    max_id = response_json["next_max_id"]
                else:
                    return {"success": True, "follower_list": required_list, "list_size": len(required_list)}
            except JSONDecodeError: return failure_response

    def follower_list_by_username(self, username: str, count: int):
        username = username.lower().strip().replace(" ", "")
        user_id_response = self.guest.get_userid(username)
        failure_response = {"success": False, "follower_list": None, "list_size": None}

        if user_id_response["success"]:
            return self.follower_list_by_userid(user_id_response["user_id"], count)
        else:
            return failure_response

    def username_of_followers_by_userid(self, user_id: str | int, count: int):
        user_id = str(user_id).strip()
        refresh_csrf_token(self)
        random_referer_username = "".join(random.choices(string.ascii_lowercase, k=6))
        request_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-prefers-color-scheme": self.preferred_color_scheme,
            "sec-ch-ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Google Chrome\";v=\"114\"",
            "sec-ch-ua-full-version-list": "\"Not.A/Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"114.0.5735.91\", \"Google Chrome\";v=\"114.0.5735.91\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"15.0.0\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "viewport-width": "1475",
            "x-asbd-id": "198387",
            "x-csrftoken": self.csrf_token,
            "x-ig-app-id": self.insta_app_id,
            "x-ig-www-claim": self.x_ig_www_claim,
            "x-requested-with": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/{random_referer_username}/followers/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

        failure_response = {"success": False, "follower_usernames": None, "list_size": None}
        max_id = ""
        required_list = []

        while True:
            if max_id != "":
                max_id_text = f"&max_id={max_id}"
            else:
                max_id_text = ""

            http_response = self.request_session.get(f"https://www.instagram.com/api/v1/friendships/{user_id}/followers/?count={30}{max_id_text}&search_surface=follow_list_page", headers=request_headers)

            try:
                response_json = http_response.json()

                if "status" not in response_json or "users" not in response_json:
                    return failure_response

                if response_json["status"] != "ok":
                    return failure_response

                for each_item in response_json["users"]:
                    if len(required_list) < count or count == 0:
                        if "username" in each_item:
                            required_list.append(each_item["username"])
                        else:
                            return failure_response

                if (len(required_list) < count or count == 0) and "next_max_id" in response_json:
                    max_id = response_json["next_max_id"]
                else:
                    return {"success": True, "follower_usernames": required_list, "list_size": len(required_list)}
            except JSONDecodeError: return failure_response

    def username_of_followers_by_username(self, username: str, count: int):
        username = username.lower().strip().replace(" ", "")
        user_id_response = self.guest.get_userid(username)
        failure_response = {"success": False, "follower_usernames": None, "list_size": None}

        if user_id_response["success"]:
            return self.username_of_followers_by_userid(user_id_response["user_id"], count)
        else:
            return failure_response

    def userid_of_followers_by_userid(self, user_id: str | int, count: int):
        user_id = str(user_id).strip()
        refresh_csrf_token(self)
        random_referer_username = "".join(random.choices(string.ascii_lowercase, k=6))
        request_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-prefers-color-scheme": self.preferred_color_scheme,
            "sec-ch-ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Google Chrome\";v=\"114\"",
            "sec-ch-ua-full-version-list": "\"Not.A/Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"114.0.5735.91\", \"Google Chrome\";v=\"114.0.5735.91\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"15.0.0\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "viewport-width": "1475",
            "x-asbd-id": "198387",
            "x-csrftoken": self.csrf_token,
            "x-ig-app-id": self.insta_app_id,
            "x-ig-www-claim": self.x_ig_www_claim,
            "x-requested-with": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/{random_referer_username}/followers/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

        failure_response = {"success": False, "follower_user_ids": None, "list_size": None}
        max_id = ""
        required_list = []

        while True:
            if max_id != "":
                max_id_text = f"&max_id={max_id}"
            else:
                max_id_text = ""

            http_response = self.request_session.get(f"https://www.instagram.com/api/v1/friendships/{user_id}/followers/?count={30}{max_id_text}&search_surface=follow_list_page", headers=request_headers)

            try:
                response_json = http_response.json()

                if "status" not in response_json or "users" not in response_json:
                    return failure_response

                if response_json["status"] != "ok":
                    return failure_response

                for each_item in response_json["users"]:
                    if len(required_list) < count or count == 0:
                        if "pk" in each_item:
                            required_list.append(each_item["pk"])
                        else:
                            return failure_response

                if (len(required_list) < count or count == 0) and "next_max_id" in response_json:
                    max_id = response_json["next_max_id"]
                else:
                    return {"success": True, "follower_user_ids": required_list, "list_size": len(required_list)}
            except JSONDecodeError: return failure_response

    def userid_of_followers_by_username(self, username: str, count: int):
        username = username.lower().strip().replace(" ", "")
        user_id_response = self.guest.get_userid(username)
        failure_response = {"success": False, "follower_user_ids": None, "list_size": None}

        if user_id_response["success"]:
            return self.userid_of_followers_by_userid(user_id_response["user_id"], count)
        else:
            return failure_response
