file2.txt b.txt c.txt file3.txt: a.txt
	{0} file3.txt
	{0} file2.txt
	shellcmd a.txt b.txt
	shellcmd b.txt >c.txt
.IGNORE: file2.txt