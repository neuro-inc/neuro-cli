#!/bin/bash
#
# Bash-completion for neuro command line client
alias errcho='echo >> log'
######################################################################
# Adds whitespace to tok unless it ends with /
# $1: tok
######################################################################
_neuro_add_whitespace()
{
    local tok=$1
    if [[ $tok = */ ]]
    then
	echo "$tok"
    else
	echo "$tok "
    fi
    return 0
} # _neuro_add_whitespace()

######################################################################
# Quotes tok, so it can be used in bash-completion
# $1: tok
######################################################################
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

######################################################################
# Generates possible completions of cur from toks
# $1: toks
# $2: cur
######################################################################
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

######################################################################
# Generates possible completions for cur from local filesystem.
# Ported from common completion extensions for bash 3 compatibility.
# $1: -d if only directories should be completed
#     -a if files should be completed as well
# $2: cur
######################################################################
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

######################################################################
# Lists all jobs of the current status (all jobs if no status given).
# [$1]: status
######################################################################
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

######################################################################
# Lists all possible completions of cur from the storage filesystem.
# $1: cur
# [$2]: y if only dicetories should be used for completion.
######################################################################
_neuro_complete-storage()
{
    local cur=$1
    local dironly=$2
    local path=
    local file=
    local prefix=
    if [[ $cur == */ ]] || [[ $cur == "" ]]
    then
	path=$cur
    else
	path=$(dirname $cur)
	file=$(basename $cur)
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

######################################################################
# Lists all possible completions of cur from the local filesystem.
# $1: cur
# [$2]: y if only dicetories should be used for completion.
######################################################################
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

######################################################################
# Lists all possible completions of cur as uri.
# $1: cur
# [$2]: y if both local and storage are the valid tareget (otherwise
#       only storage scheme is valid for completion)
# [$3]: y if only directories should be used for completion.
######################################################################
_neuro_complete-uri()
{
    local cur=$1
    local target_local=$2
    local dironly=$3
    local toks=
    if [[ "storage\://" == "$cur"*/ ]]
    then
	toks="$toks storage\://"
    fi 
    if [[ $cur == "storage\\://"* ]]
    then
	local path=${cur#storage\\://}
	local newtoks=$(_neuro_complete-storage "$path" "$dironly")
	toks="$toks $newtoks"
    fi

    if [[ $target_local == 'y' ]]
    then
	if [[ "file\\://" == "$cur"*/ ]]
	then
	    toks="$toks file\://"
	fi 

	local path=

	if [[ $cur == "file\\://"* ]]
	then
	    path=${cur#file\\://}
	elif [[ "file\\://" == "$cur"* ]]
	then
	    path=""
	else
	    path=$cur
	fi
	toks="$toks $(_neuro_complete-path "$path" $dironly)"
    fi
    echo $toks
    return 0
} # _neuro_complete-uri()

######################################################################
# Main function for completion
######################################################################
_neuro-completion()
{
    errcho "completing"
    toks=()  # array to accumulate possible completions
    cur=${COMP_WORDS[COMP_CWORD]}  # current word
    local state=init
    for i in `seq 0 $((COMP_CWORD - 1))`	     
    do
	local cword=${COMP_WORDS[i]}
	errcho "i=$i, istate=$state, cword=$cword"
	local recursive=n
	case $state in
	    init)
		case $cword in
		    neuro)
			state=base
			;;
		    *)
			state=init
		esac
		;;
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
		    completion)
			state=completion
			;;
		    *)
			state=error
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
		    *)
			state=erro
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
		    *)
			state=error
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
		    *)
			state=error
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
		    --http)
			state=model-train-http
			;;
		    --ssh)
			state=model-train-ssh
			;;
		    --quite|-q)
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
			state=done
			;;
		    id_rsa)
			state=config-id_rsa
			;;
		    *)
			state=error
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
			state=done
			;;
		    *)
			state=error
			;;
		esac
		;;
	    completion)
		case $cword in
		    generate)
			state=done
			;;
		    patch)
			state=done
			;;
		    *)
			state=error
			;;
		esac
		;;
        esac
    done
    errcho "State=$state"
    case $state in
	base)
	    toks='-u --url -t --token -v --verbose
                  -v --version model job store help 
		  config image completion'
	    ;;
	url)
	    toks='http\://'
	    ;;
	token)
	    ;;
	model)
	    toks='train'
	    ;;
	model-train)
	    toks='-c --cpu -g --gpu -m --memory -x --extshm
	    	  --http --ssh -q --quite'	     
	    ;;
	model-train-dataset)
	    toks=$(_neuro_complete-uri "$cur" n y)
	    ;;
	model-train-result)
	    toks=$(_neuro_complete-uri "$cur" n y)
	    ;;
	model-train-ssh)
	    ;;
	model-train-http)
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
	    toks='url auth show id_rsa'
	    ;;
	config-url)
	    toks='http\://'
	    ;;
	config-auth)
	    ;;
	config-id_rsa)
	    toks=$(_neuro_complete-uri "$cur" y n)
	    ;;
	image)
	    toks='push pull'
	    ;;
	completion)
	    toks='generate patch'
	    ;;
    esac
    _neuro_gen_completion "$toks" "$cur"
    return 0
} # _neuro_completion()

complete -o nospace -F _neuro-completion neuro

