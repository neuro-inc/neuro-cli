#!/bin/bash
#
# Bash-completion for neuro command line client
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

_neuro_complete-status()
{
    local toks="all"
    local statuses="pending running succeeded failed"
    for s1 in $statuses
    do
	toks="$toks $s1"
	for s2 in $statuses
	do
	    if [[ $s1 == $s2 ]]
	    then
		continue
	    fi
	    toks="$toks $s1,$s2"
	    for s3 in $statuses
	    do
		if [[ $s1 == $s3 ]] || [[ $s2 == $s3 ]]
		then
		    continue
		fi
		toks="$toks $s1,$s2,$s3"
	    done
	done
    done
    echo $toks
    return 0
} # _neuro_complete-status

######################################################################
# Main function for completion
######################################################################
_neuro-completion()
{
    toks=()  # array to accumulate possible completions
    cur=${COMP_WORDS[COMP_CWORD]}  # current word
    local state=init
    for i in `seq 0 $((COMP_CWORD - 1))`
    do
	local cword=${COMP_WORDS[i]}
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
		    share)
			state=share
			;;
		    help)
			state=base
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
	    model)
		case $cword in
		    train)
			state=model-train
			;;
		    debug)
			state=model-debug
			;;
		    *)
			state=error
			;;
		esac
		;;
	    model-train)
		case $cword in
		    -g|--gpu)
			state=model-train-gpu
			;;
		    --gpu-model)
			state=model-train-gpu-model
			;;
		    -c|--cpu)
			state=model-train-cpu
			;;
		    -m|--memory)
			state=model-train-memory
			;;
		    -x|--extshm)
			;;
		    --http)
			state=model-train-http
			;;
		    --ssh)
			state=model-train-ssh
			;;
		    -d|--description)
			state=model-train-description
			;;
		    --q|--quite)
			;;
		    *)
			state=model-train-dataset
			;;
		esac
		;;
	    model-train-memory|model-train-gpu|model-train-cpu)
		state=model-train
		;;
	    model-train-http|model-train-ssh|model-train-gpu-model)
		state=model-train
		;;
	    model-train-description)
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
	    model-debug)
		case $cword in
		    --localport)
			state=model-debug-localport
		    ;;
		    *)
			state=done
		    ;;
		esac
		;;
	    model-debug-localport)
		state=model-debug
		;;
	    job)
		case $cword in
		    submit)
			state=job-submit
			;;
		    monitor)
			state=job-monitor
			;;
		    list)
			state=job-list
			;;
		    status)
			state=job-status
			;;
		    kill)
			state=job-kill
			;;
		    ssh)
			state=job-ssh
			;;
		    *)
			state=error
			;;
		esac
		;;
	    job-submit)
		case $cword in
		    -g|--gpu)
			state=job-submit-gpu
			;;
		    --gpu-model)
			state=job-submit-gpu-model
			;;
		    -c|--cpu)
			state=job-submit-cpu
			;;
		    -m|--memory)
			state=job-submit-memory
			;;
		    -x|--extshm)
			;;
		    --http)
			state=job-submit-http
			;;
		    --ssh)
			state=job-submit-ssh
			;;
		    -d|--description)
			state=job-submit-description
			;;
		    --q|--quite)
			;;
		    --volume)
			state=job-submit-volume
			;;
		    *)
			state=job-submit-cmd
		esac
		;;
	    job-submit-memory|job-submit-gpu|job-submit-cpu)
		state=job-submit
		;;
	    job-submit-http|job-submit-ssh|job-submit-gpu-model)
		state=job-submit
		;;
	    job-submit-description|job-submit-volume)
		state=job-submit
		;;
	    job-submit-cmd)
		state=job-submit-cmd
		;;
	    job-list)
		case $cword in
		    --status)
			state=job-list-status
			;;
		    *)
			state=done
			;;
		esac
		;;
	    job-list-status)
		state=done
		;;
	    job-status|job-kill|job-monitor)
		state=done
		;;
	    job-ssh)
		case $cword in
		    --user)
			state=job-ssh-user
		    ;;
		    --key)
			state=job-ssh-key
		    ;;
		esac
		;;
	    job-ssh-user|job-ssh-key)
		state=job-ssh
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
		    mv)
			state=store-mv
			;;
		    *)
			state=erro
			;;
		esac
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
	    store-mv)
		case $cword in
		    *)
			state=store-mv2
			;;
		esac
		;;
	    store-mv2)
		state=done
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
	    share)
		state=share-user
		;;
	    share-user)
		state=share-access
		;;
	    share-access)
		state=done
		;;
	esac
    done
    case $state in
	base)
	    toks='-u --url -t --token -v --verbose
		  -v --version model job store image
		  config completion share help'
	    ;;
	url)
	    toks='http\://'
	    ;;
	token)
	    ;;
	model)
	    toks='train debug'
	    ;;
	model-train)
	    toks='-c --cpu -g --gpu --gpu-model -m --memory -x --extshm
		  --http --ssh -q --quite --description'
	    ;;
	model-train-dataset)
	    toks=$(_neuro_complete-uri "$cur" n y)
	    ;;
	model-train-result)
	    toks=$(_neuro_complete-uri "$cur" n y)
	    ;;
	model-train-gpu-model|job-submit-gpu-model)
	    toks="nvidia-tesla-k80 nvidia-tesla-p4 nvidia-tesla-v100"
	    ;;
	model-debug)
	    toks=$(_neuro_listjobs running)
	    toks="$toks --localport"
	    ;;
	job)
	    toks='submit list status monitor kill'
	    ;;
	job-submit)
	    toks='-c --cpu -g --gpu --gpu-model -m --memory -x --extshm
		  --http --ssh -q --quite --volume --description'
	    ;;
	job-submit-volume)
	    toks=$(_neuro_complete-uri "$cur" n y)
	    ;;
	job-status)
	    toks=$(_neuro_listjobs)
	    ;;
	job-list)
	    toks="--status"
	    ;;
	job-list-status)
	    toks=$(_neuro_complete-status)
	    ;;
	job-kill|job-monitor)
	    toks=$(_neuro_listjobs running)
	    ;;
	job-ssh)
	    toks=$(_neuro_listjobs running)
	    toks="$toks --user --key"
	    ;;
	store)
	    toks='rm ls cp mv mkdir'
	    ;;
	store-ls|store-mkdir)
	    toks=$(_neuro_complete-uri "$cur" n y)
	    ;;
	store-rm)
	    toks=$(_neuro_complete-uri "$cur" n n)
	    ;;
	store-cp)
	    local newtoks=$(_neuro_complete-uri "$cur" y $recursive)
	    toks="-r --recursive -p --progress $newtoks"
	    ;;
	store-cp2)
	    toks=$(_neuro_complete-uri "$cur" y $recursive)
	    ;;
	store-mv)
	    toks=$(_neuro_complete-uri "$cur" n n)
	    ;;
	store-mv2)
	    toks=$(_neuro_complete-uri "$cur" n n)
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
	share)
	    toks=$(_neuro_complete-uri "$cur" n n)
	    ;;
	share-access)
	    toks="manage read write"
    esac
    _neuro_gen_completion "$toks" "$cur"
    return 0
} # _neuro_completion()

complete -o nospace -F _neuro-completion neuro
