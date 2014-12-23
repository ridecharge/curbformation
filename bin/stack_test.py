import unittest
from unittest.mock import MagicMock
from stack import Stack

class StackTest(unittest.TestCase):
	def setUp(self):
		self.cf_conn = MagicMock()
		self.stack = Stack(Stack.Types.iam, Stack.ENV_GLOBAL, self.cf_conn)

	def test_stack_name(self):
		self.assertEqual(self.stack.stack_name(), "global-iam")

	def test_template_uri(self):
		self.assertEqual(
			self.stack.template_uri(), 
			"https://s3.amazonaws.com/curbformation-global-templates/iam.json")

	def test_create_stack_called(self):
		stack = self.stack
		self.stack.create()
		self.cf_conn.create_stack.assert_called_with(
			stack.stack_name(), 
			None, 
			stack.template_uri(), 
			stack.params(), 
			capabilities=stack.capabilities())


if __name__ == '__main__':
    unittest.main()