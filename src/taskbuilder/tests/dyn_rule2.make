.taker/make_targets/rule2: file0.txt file1.txt file2.txt
	../exe1 <file1.txt
	-./exe2 <file2.txt
	./exe0 <file0.txt >file4.txt
	{0} hello/world
	{0} -p .taker/make_targets
	{1} .taker/make_targets/rule2
.SILENT: .taker/make_targets/rule2
rule2: .taker/make_targets/rule2
.PHONY: rule2

file3.txt: .taker/make_targets/rule2
