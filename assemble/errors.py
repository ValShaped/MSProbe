"""Exception types and important functions for error handling"""


def highlight(string: str, substring: str) -> str:
	"""Highlight a substring in a string"""
	return string.replace(substring, f"\033[4m{substring}\033[0m") if substring else string

class AssemblyError(Exception):
	"""
	The base class for all Assembly Exceptions
	"""
	def __init__(self, name: str, reason: str) -> None:
		self.type = "Improperly defined AssemblyError"
		self.name = name
		self.reason = reason
	def pretty_print(self, line_number: int, line: str) -> str:
		line = highlight(line, self.name)
		return f'{self.type} found on line {line_number + 1}: "{line}"\n{self.reason}'

class OpcodeError(AssemblyError):
	"""
	`OpcodeError` is raised when an opcode mnemonic is not found in the opcode map
	"""
	def __init__(self, opcode, reason = "Opcode not found in opcode map."):
		super().__init__(name=opcode, reason=reason)
		self.type = "Invalid opcode mnemonic"

class RedefinedLabelError(AssemblyError):
	"""
	`RedefinedLabelError` is raised when a label is defined multiple times in the same source file.
	Since labels are resolved after compilation, it cannot be known whether you intend to reference a past
	or future definition of a label.
	"""
	def __init__(self, label, reason = "Label already defined."):
		super().__init__(name=label, reason=reason)
		self.type = "Redefined Label"
	def pretty_print(self, line_number: int, _line: str = "") -> str:
		return f'Label "{self.name}" at line number {str(line_number + 1)} already defined'

class UndefinedLabelError(AssemblyError):
	"""
	`UndefinedLabelError` is raised when a label used in a jump instruction is not defined in the source
	"""
	def __init__(self, operand: str, reason: str):
		super().__init__(name=operand, reason=reason)
		self.type = "Undefined label"

class AddressingModeError(AssemblyError):
	"""
	`AddressingModeError` is raised when the operand of an instruction is specified with an
	unrepresentable addressing mode.
	"""
	def __init__(self, operand: str, reason: str):
		super().__init__(name=operand, reason=reason)
		self.type = "Invalid addressing mode"

class JumpOffsetError(AssemblyError):
	"""
	`JumpOffsetError` is raised when a jump offset cannot be encoded.
	Jump offsets are a 12 bit signed integer representing the number of processor words to jump.
	As such, they can only encode jump offsets from -0x3fe to +0x400
	"""
	def __init__(self, offset: str, reason: str):
		super().__init__(name=offset, reason=reason)
		self.type = "Invalid jump offset"

class RegisterError(AssemblyError):
	"""
	`RegisterError` is raised when a register isn't one of
	[`pc`, `sp`, `sr`, `cg`, `r0`, ..., `r15`]
	"""
	def __init__(self, register: str, reason: str = "Valid registers are pc, sp, sr, cg, or r0-r15."):
		super().__init__(name=register, reason=reason)
		self.type = "Invalid register mnemonic"
