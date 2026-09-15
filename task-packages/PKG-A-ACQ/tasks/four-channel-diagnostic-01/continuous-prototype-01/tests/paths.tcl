puts "PATH_PROBE cwd=[pwd] argc=$argc argv=$argv"
foreach a $argv {puts "argument=<$a> normalized=<[file normalize $a]> exists=[file exists $a]"}
