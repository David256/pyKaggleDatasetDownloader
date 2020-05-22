#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import re
import hashlib
import base64
import pathlib
import argparse

endpoint = "https://www.kaggle.com"
method = "/api/v1"
url_path = "/datasets/download/{owner_slug}/{dataset_slug}"

header_params = {
	"Accept": "file",
	"User-Agent": "Swagger-Codegen/1/python"
}

class KaggleDatasetDownloader(object):
	def __init__(self, user, key, verbose=False):
		super(KaggleDatasetDownloader, self).__init__()
		self.user = user
		self.key = key
		self.verbose = verbose
		self.session = requests.Session()
		self.session.auth = (self.user, self.key)

	def download(self, url, path=None, filename=None, check_md5=False):
		owner_slug, dataset_slug = self._get_data_from_url(url)

		if self.verbose:
			print("URL:", url)

		# Connect to Kaggle
		if self.verbose:
			print("Connecting...")
		web = self.session.get(
			endpoint + method + url_path.format(
				owner_slug=owner_slug,
				dataset_slug=dataset_slug),
			headers=header_params)

		# Show HTTP response
		if self.verbose:
			print(web.status_code, web.reason)

		# Check if all thing is ok
		if not web.ok:
			return False

		if self.verbose:
			print("Content-Disposition:", web.headers.get("Content-Disposition", ""))
			print("x-goog-hash:", web.headers.get("x-goog-hash", ""))

		if not filename:
			# Search a filename
			filename = re.search(
				r'(?<=(filename=))([\w\.\-]+)',
				web.headers.get("Content-Disposition", ""))

			# Complete missing data for the filename
			if not filename:
				filename = "dataset.downloaded"
			else:
				filename = filename.group()

		if check_md5:
			# Search an MD5
			md5 = re.search(
				r'(?<=(md5\=))([a-zA-Z0-9=\+\/]+)',
				web.headers.get("x-goog-hash", ""))

			# Complete missing data for MD5
			if md5:
				md5 = md5.group()
				md5 = md5.encode()
				# Original MD5 in Base64
				if self.verbose:
					print(f"md5: {md5}")
				# Original MD5
				md5 = base64.b64decode(md5)
				if self.verbose:
					print(f"md5: {md5}")

		# Start downloading
		filepath = pathlib.Path(
			path or "",
			filename)
		if self.verbose:
			print(f"downloading to {filepath}...")
		# Open the file
		with open(filepath, "wb") as file:
			for part in web.iter_content(chunk_size=2048):
				file.write(part)
		# Check MD5 if it is configured
		if check_md5:
			if md5:
				with open(filepath, "rb") as file:
					md5_original = hashlib.md5(file.read()).digest()
					print(
						"MD5",
						"is" if md5 == md5_original else "is not",
						"correct.")
					return (md5 == md5_original)
			else:
				print("MD5 check has not been done.")
				return True
		else:
			return True

	def _get_data_from_url(self, url):
		searched = re.match(
			r"(https?://)?www\.kaggle\.com/([\w\-]+)/([\w\-]+)",
			url)
		if not searched:
			raise ValueError("URL not valid")
		_, owner_slug, dataset_slug = searched.groups()
		return owner_slug, dataset_slug


if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description="This simple software lets you download datasets from Kaggle using your credentials (API Token).")
	parser.add_argument(
		"url",
		help="Kaggle URL")
	parser.add_argument(
		"user",
		help="Kaggle user")
	parser.add_argument(
		"key",
		help="Your API Token")
	parser.add_argument(
		"filepath",
		nargs="?",
		default=None,
		help="The filepath")
	parser.add_argument(
		"--check-md5",
		nargs="?",
		dest="check_md5",
		default=False,
		const=True,
		help="Enable check MD5")
	parser.add_argument(
		"-v",
		"--verbose",
		dest="verbose",
		nargs="?",
		default=False,
		const=True,
		help="Enable verbose")
	args = parser.parse_args()

	# New object
	kdd = KaggleDatasetDownloader(args.user, args.key, args.verbose)
	success = kdd.download(
		args.url,
		pathlib.os.path.dirname(args.filepath) if args.filepath else None,
		pathlib.os.path.basename(args.filepath) if args.filepath else None,
		args.check_md5)

	if success:
		print("downloading successfully.")
	else:
		print("downloading failed")