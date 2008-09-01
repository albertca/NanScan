import tempfile
import os

## @brief Simplify the task of creating and managing temporary files in a 
# secure manner.
# 
# Although python already provides functions for creating temporary files
# in nanscan we usually need only the filename and this is passed as a parameter
# to external applications such as convert or tesseract. Using those file names
# in this cases would still make the application vulnerable to race conditions
# so we need a temporary directory in which all such files are created.
# This class ensures this directory is created and one can savely manage temporary
# files.
class TemporaryFile:
	directory = None

	## @brief Creates a temporary file securely.
	# If the temporary directory doesn't exist or has been deleted it's created.
	# This will allow the user to remove the directory at 'almost' any time
	# without breaking the application, though a way to easily remove temp files 
	# should be provided, probably.
	@staticmethod
	def create( suffix='' ):
		if not TemporaryFile.directory or not os.path.exists( TemporaryFile.directory ):
			TemporaryFile.directory = tempfile.mkdtemp()
		fd, name = tempfile.mkstemp( suffix=suffix, dir=TemporaryFile.directory )
		return name
