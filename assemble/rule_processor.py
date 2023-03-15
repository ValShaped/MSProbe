from common import isHexadecimal
from typing import Callable
import re

class RuleProcessor:
	def __init__(self):
		self.rules = []
	def __call__ (self, args: any) -> any:
		for rule in self.rules:
			if not args: break
			args = rule(args)
		return args
	def register(self, rule: Callable):
		if rule not in self.rules:
			self.rules.append(rule)

def directive_org(args: str) -> str:
	global PC
	if isHexadecimal(args):
		PC = int(args, 16)
		print(f'{PC = }')
	return ''

# Directive handles .directives
class Directive(RuleProcessor):
	"""Directive: Process and handle .directive statements"""
	def __init__(self):
		#A directive is a '.' followed by a directive identifier, followed by an optional set of arguments
		super().__init__()
		self._expression = re.compile(r"[.](\w+)\s*([^;/]*)")
		self._define = Define()
		self.rules = {
			'define': self._define.register,
			'def': self._define.register,
			'org': directive_org,
			'end': lambda _: None,
		}

	def __call__(self, line: str) -> str | None:
		if not line:
			return line
		match = re.match(self._expression, line)
		if not match:
			return line
		directive, args = match.groups()
		#Handle .directives
		if directive in self.rules:
			line = self.rules[directive](args)
		return line

# -- Defines --
class Define(RuleProcessor):
	"""
	# Define
	Handles data storage and callbacks for .define processing.
	```asm
	.define identifier [text...]
	```
	Automatically registered by Directive during init.
	"""
	def __init__(self) -> None:
		self.rules = {}

	def __call__(self, ins: str) -> str:
		for define in self.rules:
			ins = ins.replace(define, self.rules[define])
		return ins

	def register(self, argument: str):
		"""
		Registers a define for replacement on subsequent lines.
		"""
		#Define is of format .define [identifier] [any text]
		#Space(s) not required, but if spaces are not used, ':' or '=' must be used in its place
		define = re.match(r'(\w+)[\s:=]+(.*)\s*', argument)
		if define:
			label, replacement = define.groups()
			self.rules[label] = replacement
			preprocessor.register(self)
		return ""

#Instantiate default rule processors:
preprocessor  = RuleProcessor()  #Run for every line before parsing
"""
preprocessor: Rule Processor responsible for pre-processing lines of source.

To add additional functionality, call preprocessor.register(Callable),
and pass in a function with the following signature:
```py
def preprocessor_rule(instruction_line: str) -> str | None:
```
Note that returning None will stop line parsing.
"""
postprocessor = RuleProcessor() #Run once per source file after parsing

_directive = Directive()
preprocessor.register(_directive)
