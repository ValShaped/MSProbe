"""Functions that are useful in multiple places, such as converting hexadecimal to binary and back."""

import re

def bitrep(number, bits = 16):
	"""Converts to binary form, fixing leading zeroes."""
	mask = int('0b' + '1' * bits, 2)
	binstr = str(bin(number & mask))[2:]
	#negative = binstr[0] == '-'
	bitcount = len(binstr)
	leading0s = bits - bitcount
	return ('0' * leading0s) + binstr

def hexrep(number, zeroes = 4):
	"""Converts to hex form, fixing leading zeroes."""
	mask = int('0b' + '1' * (zeroes * 4), 2)
	hexstr = hex(number & mask)[2:]
	hexcount = len(hexstr)
	leading0s = zeroes - hexcount
	return ('0' * leading0s) + hexstr

def isHexadecimal(string: str) -> bool:
	"""Determines if a number is hexadecimal"""
	return (re.fullmatch(r'[-+]?(0[xX])?[\dA-Fa-f]+', string) is not None)
