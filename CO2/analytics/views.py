from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse

import pandas as pd
import numpy as np
from datetime import datetime
import scipy


def index(request):
    return HttpResponse("Hello, world. You're at the analytics index.")