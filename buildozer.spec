[app]
title = PetApp
package.name = petapp
package.domain = org.example
source.dir = .
source.include_exts = py,tflite
version = 1.0

requirements = python3, kivy, tensorflow-lite, ipfshttpclient, requests, android

android.add_jars = libs/tensorflow-lite.aar

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, ACCESS_NETWORK_STATE

android.api = 31
android.minapi = 21
android.sdk = /home/user/android-sdk
android.ndk_path = /home/user/android-ndk
android.ndk_version = 25.2.9519653
android.archs = arm64-v8a

android.accept_sdk_license = True
android.bootstrap = sdl2
log_level = 2
warn_on_root = 0
