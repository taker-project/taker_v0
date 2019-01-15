.taker/make_targets/hello: world
	echo hello
	{0} -p .taker/make_targets
	{1} .taker/make_targets/hello
hello: .taker/make_targets/hello
.PHONY: hello