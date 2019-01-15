default:
	true
.PHONY: default

help:
	echo 'Available commands:'
	echo '                help: Prints this help'
	echo '              descr1: rule 1 with description'
	echo '              descr2: rule 2 with description'
.PHONY: help

descr1: .taker/make_targets/descr2
	echo here
.PHONY: descr1

.taker/make_targets/descr2:
	echo here
	{0} -p .taker/make_targets
	{1} .taker/make_targets/descr2
descr2: .taker/make_targets/descr2
.PHONY: descr2

nodescr1: .taker/make_targets/descr2 descr1 file1.txt
	./exe1 file1.txt
	{2} 2>/dev/null
.PHONY: nodescr1

.taker/make_targets/nodescr2:
	{0} -p .taker/make_targets
	{1} .taker/make_targets/nodescr2
nodescr2: .taker/make_targets/nodescr2
.PHONY: nodescr2
