import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os
import tempfile
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import uuid
import json
from datetime import datetime

# MCC Codes dictionary
MCC_CODES = {
    '5411': 'Grocery Stores',
    '5542': 'Gas Stations',
    '5812': 'Restaurants',
    '5814': 'Fast Food',
    '5912': 'Drug Stores',
    '5311': 'Department Stores',
    '5661': 'Shoe Stores',
    '5699': 'Clothing Stores',
    '7832': 'Movie Theaters',
    '5999': 'Miscellaneous Retail',
    '4111': 'Transportation',
    '7011': 'Hotels',
    '4121': 'Taxis/Rideshares',
    '5732': 'Electronics',
    '8011': 'Medical Services',
    '8021': 'Dental Services',
    '8099': 'Health Services',
    '8299': 'Educational Services',
    '4816': 'Online Services',
    '5945': 'Hobby/Toy Stores',
    '5094': 'Office Supplies',
    '5941': 'Sporting Goods',
    '7999': 'Recreation Services',
    '7230': 'Beauty/Barber Shops',
    '
