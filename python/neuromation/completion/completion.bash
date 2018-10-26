#/usr/bin/env bash
alias errcho='>>log echo'

_neuro_add_whitespace()
{
    local word=$1
    if [[ $word = */ ]]
    then
	echo "$word"
    else
	echo "$word "
    fi
    return 0
} # _neuro_add_whitespace()

_neuro_quote()  {
    local tok=$1
    tok=$(printf "%q" "$tok")
    if [[ $tok == *"\\\\:"* ]]
    then
	local pref=${tok%\\\\:*}
	tok="$pref${tok#$pref\\}"
    fi
    echo $tok
    return 0
} # _neuro_quote()

_neuro_gen_completion() {
    local toks=$1
    local cur=$2
    COMPREPLY=()
    for tok in $toks
    do
	local qtok="$(_neuro_quote $tok) "
	if [[ $tok == "$cur"* ]] || [[ $qtok == "$cur"* ]]
	then
	    COMPREPLY+=( "$(_neuro_add_whitespace $qtok)" )
	fi
    done
    return 0
} # _neuro_gen_completion()

_neuro_filedir()
{
    local cur=$2

    local -a toks
    local x tmp
 
    x=$( compgen -d -- "$cur" ) &&
    while read -r tmp; do
        toks+=( "$tmp/" )
    done <<< "$x"
    if [[ "$1" != -d ]]; then
        local quoted=$(_neuro_quote $cur)
	
        local xspec=${1:+"!*.@($1)"}
	if [[ "$1" = -a ]]
	then
	    xspec="!*"
	fi
        x=$( compgen -f -X "$xspec" -- $quoted ) &&
        while read -r tmp; do
	    if [[ -d "$tmp" ]]
	    then
		continue
	    fi
	    toks+=( "$tmp" )
        done <<< "$x"
    fi
    echo "${toks[@]}"
    return 0
} # _neuro_filedir()

_neuro_listjobs()
{
    status=$1
    
    local neurocmd="neuro job list"

    local words=
    while read -r line
    do
	local arrline=($line)
	local jobid=${arrline[0]}
	local jobstat=${arrline[1]}
	if [[ $status == "" ]] || [[ $jobstat == $status ]]
	then
	    words="$words $jobid"
	fi
    done < <($neurocmd)
    echo $words
    return 0
} # _neuro_listjobs()

_neuro_complete-storage()
{
    local fullpath=$1
    local dironly=$2
    local path=
    local file=
    local prefix=
    if [[ $fullpath == */ ]] || [[ $fullpath == "" ]]
    then
	path=$fullpath
    else
	path=$(dirname $fullpath)
	file=$(basename $fullpath)
    fi
    path=${path#.}
    path=${path#/}
    path=${path%/}
    if [[ $path == '' ]]
    then 
	prefix="storage\://"
    else 
	prefix="storage\://$path/"
    fi
    if [[ $path == "" ]]; then path=.; fi
    local neurocmd="neuro store ls storage://$path"
    local dircontent=($($neurocmd))
    local toks=

    local line
    while read -r line
    do
	local arrline=($line)
	local type=${arrline[0]}
	local name=${arrline[2]}
	if [[ $type = "directory" ]]
	then
	    name="$name"/
	else
	    if [[ $dironly = y ]]
	    then
		continue
	    fi
	fi
	toks="$toks $prefix$name"
    done < <($neurocmd)
    echo $toks
    return 0
} # _neuro_complete-storage()

_neuro_complete-path()
{
    local path=$1
    local dironly=$2
    if [[ $dironly == 'y' ]]
    then
	_neuro_filedir -d "$path"
    else
	_neuro_filedir -a "$path"
    fi
    return 0
} # _neuro_complete-path()

_neuro_complete-uri()
{
    local uri=$1
    local target_local=$2
    local dironly=$3
    local toks=
    if [[ "storage\://" == "$uri"*/ ]]
    then
	toks="$toks storage\://"
    fi 
    if [[ $uri == "storage\\://"* ]]
    then
	local path=${uri#storage\\://}
	local newtoks=$(_neuro_complete-storage "$path" "$dironly")
	toks="$toks $newtoks"
    fi

    if [[ $target_local == 'y' ]]
    then
	if [[ "file\\://" == "$uri"*/ ]]
	then
	    toks="$toks file\://"
	fi 

	local path=

	if [[ $uri == "file\\://"* ]]
	then
	    path=${uri#file\\://}
	elif [[ "file\\://" == "$uri"* ]]
	then
	    path=""
	else
	    path=$uri
	fi
	toks="$toks $(_neuro_complete-path "$path" $dironly)"
    fi
    echo $toks
    return 0
} # _neuro_complete-uri()

# Main function for completion
_neuro-completion()
{
    toks=()  # global array to accumulate possible completions
    cur=${COMP_WORDS[COMP_CWORD]}  # current word
    local state=base
    for i in `seq 1 $((COMP_CWORD - 1))`	     
    do
	local cword=${COMP_WORDS[i]}
	local recursive=n
	case $state in
	    base)
		case $cword in
		    -v|--verbose|--version)
			state=base
			;;
		    -u|--url)
			state=url
			;;
		    -t|token)
			state=token
			;;
		    model)
			state=model
			;;
		    job)
			state=job
			;;
		    store)
			state=store
			;;
		    config)
			state=config
			;;
		    image)
			state=image
			;;
		esac
		;;
	    store)
		case $cword in
		    ls)
			state=store-ls
			;;
		    rm)
			state=store-rm
			;;
		    mkdir)
			state=store-mkdir
			;;
		    cp)
			state=store-cp
			;;
		esac
		;;
	    job)
		case $cword in
		    list)
			state=done
		    ;;
		    status)
			state=job-status
		    ;;
		    kill)
			state=job-kill
		    ;;
		    monitor)
			state=job-monitor
			;;
		esac
		;;
            url)
		state=base
		;;
	    token)
		state=base
		;;
	    store-ls|store-rm|store-mkdir)
		state=done
		;;
	    store-cp)
		case $cword in
		    -r|--recursive)
			recursive=y
			;;
		    *)
			state=store-cp2
			;;
		esac
		;;
	    job-status|job-kill|job-monitor)
		state=done
		;;
	    model)
		case $cword in
		    train)
			state=model-train
			;;
		    test|infer)
			;;
		esac
		;;
	    model-train)
		case $cword in
		    -c|--cpu)
			state=model-train-cpu
			;;
		    -g|--gpu)
			state=model-train-gpu
			;;
		    -m|--memory)
			state=model-train-memory
			;;
		    -x|--extshm)
			;;
		    *)
			state=model-train-dataset
			;;
		esac
		;;
	    model-train-memory|model-train-gpu|model-train-cpu)
		state=model-train
		;;
	    model-train-dataset)
		state=model-train-result
		;;
	    model-train-result)
		state=model-train-cmd
		;;
	    model-train-cmd)
		state=model-train-cmd
		;;
	    config)
		case $cword in
		    url)
			state=config-url
			;;
		    auth)
			state=config-auth
			;;
		    show)
			state=final
			;;
		esac
		;;
	    image)
		case $cword in
		    push)
			state=config-pull
			;;
		    pull)
			state=config-push
			;;
		    search)
			state=final
			;;
		esac
        esac
    done
    case $state in
	base)
	    toks='-u --url -t --token -v --verbose
                  -v --version model job store help 
		  config image'
	    ;;
	url)
	    toks='http\://'
	    ;;
	token)
	    ;;
	model)
	    toks='train test infer'
	    ;;
	model-train)
	    toks='-c --cpu -g --gpu -m --memory -x --extshm'
	    ;;
	model-train-dataset)
	    toks=$(_neuro_complete-uri "$cur" n y)
	    ;;
	model-train-result)
	    toks=$(_neuro_complete-uri "$cur" n y)
	    ;;
	job)
	    toks='list status monitor kill'
	    ;;
	job-status)
	    toks=$(_neuro_listjobs)
	    ;;
	job-kill|job-monitor)
	    toks=$(_neuro_listjobs running)
	    ;;
	store)
	    toks='ls cp rm mkdir'
	    ;;
	store-ls|store-mkdir)
	    toks=$(_neuro_complete-uri "$cur" n y)
	    ;;
	store-rm)
	    toks=$(_neuro_complete-uri "$cur" n n)
	    ;;
	store-cp)
	    local newtoks=$(_neuro_complete-uri "$cur" y $recursive)
	    toks="-r --recursive $newtoks"
	    ;;
	store-cp2)
	    toks=$(_neuro_complete-uri "$cur" y $recursive)
	    ;;
	config)
	    toks='url auth show'
	    ;;
	config-url)
	    toks='http\://'
	    ;;
	config-auth)
	    ;;
	image)
	    toks='push pull search'
	    ;;
    esac
    _neuro_gen_completion "$toks" "$cur"
    return 0
} # _neuro_completion()

complete -o nospace -F _neuro-completion neuro

