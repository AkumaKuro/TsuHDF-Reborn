from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

from . import mod_only

__all__ = [
    'ooc_cmd_bg',
    'ooc_cmd_bglock',
    'ooc_cmd_allow_iniswap',
    'ooc_cmd_allow_blankposting',
    'ooc_cmd_allow_showname',
    'ooc_cmd_force_nonint_pres',
    'ooc_cmd_status',
    'ooc_cmd_area',
    'ooc_cmd_getarea',
    'ooc_cmd_getareas',
    'ooc_cmd_area_lock',
    'ooc_cmd_area_spectate',
    'ooc_cmd_area_unlock',
    'ooc_cmd_link',
    'ooc_cmd_removelink',
    'ooc_cmd_update',
    'ooc_cmd_invite',
    'ooc_cmd_uninvite',
    'ooc_cmd_area_kick',
    'ooc_cmd_getafk',
    'ooc_cmd_delay'
]


def ooc_cmd_bg(client, arg):
    """
    Set the background of a room.
    Usage: /bg <background>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a name. Use /bg <background>.')
    if not client.is_mod and client.area.bg_lock == "true":
        raise AreaError("This area's background is locked!")
    elif client.area.cannot_ic_interact(client):
        raise AreaError("You are not permitted to change the background in this area!")
    try:
        client.area.change_background(arg)
    except AreaError:
        raise
    client.area.broadcast_ooc(
        f'{client.char_name} changed the background to {arg}.')
    database.log_room('bg', client, client.area, message=arg)


@mod_only()
def ooc_cmd_bglock(client, arg):
    """
    Toggle whether or not non-moderators are allowed to change
    the background of a room.
    Usage: /bglock
    """
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    # XXX: Okay, what?
    if client.area.bg_lock == "true":
        client.area.bg_lock = "false"
    else:
        client.area.bg_lock = "true"
    client.area.broadcast_ooc(
        '{} [{}] has set the background lock to {}.'.format(
            client.char_name, client.id, client.area.bg_lock))
    database.log_room('bglock', client, client.area, message=client.area.bg_lock)


@mod_only()
def ooc_cmd_allow_iniswap(client, arg):
    """
    Toggle whether or not users are allowed to swap INI files in character
    folders to allow playing as a character other than the one chosen in
    the character list.
    Usage: /allow_iniswap
    """
    client.area.iniswap_allowed = not client.area.iniswap_allowed
    answer = 'allowed' if client.area.iniswap_allowed else 'forbidden'
    client.send_ooc(f'Iniswap is {answer}.')
    database.log_room('iniswap', client, client.area, message=client.area.iniswap_allowed)


@mod_only(area_owners=True)
def ooc_cmd_allow_blankposting(client, arg):
    """
    Toggle whether or not in-character messages purely consisting of spaces
    are allowed.
    Usage: /allow_blankposting
    """
    client.area.blankposting_allowed = not client.area.blankposting_allowed
    answer = 'allowed' if client.area.blankposting_allowed else 'forbidden'
    client.area.broadcast_ooc(
        '{} [{}] has set blankposting in the area to {}.'.format(
            client.char_name, client.id, answer))
    database.log_room('blankposting', client, client.area, message=client.area.blankposting_allowed)

@mod_only()
def ooc_cmd_allow_showname(client, arg):
    """
    Toggle whether or not users can use shownames in the current area.
    Usage: /allow_showname
    """
    client.area.showname_changes_allowed = not client.area.showname_changes_allowed
    answer = 'allowed' if client.area.showname_changes_allowed else 'forbidden'
    client.area.broadcast_ooc(
        '{} [{}] has set showname usage in the area to {}.'.format(
            client.char_name, client.id, answer))
    database.log_room('shownames', client, client.area, message=client.area.showname_changes_allowed)

@mod_only(area_owners=True)
def ooc_cmd_force_nonint_pres(client, arg):
    """
    Toggle whether or not all pre-animations lack a delay before a
    character begins speaking.
    Usage: /force_nonint_pres
    """
    client.area.non_int_pres_only = not client.area.non_int_pres_only
    answer = 'non-interrupting only' if client.area.non_int_pres_only else 'non-interrupting or interrupting as you choose'
    client.area.broadcast_ooc(
        '{} [{}] has set pres in the area to be {}.'.format(
            client.char_name, client.id, answer))
    database.log_room('force_nonint_pres', client, client.area, message=client.area.non_int_pres_only)


def ooc_cmd_status(client, arg):
    """
    Show or modify the current status of a room.
    Usage: /status <idle|rp|casing|looking-for-players|lfp|recess|gaming>
    """
    if len(arg) == 0:
        client.send_ooc(f'Current status: {client.area.status}')
    else:
        try:
            client.area.change_status(arg)
            client.area.broadcast_ooc('{} changed status to {}.'.format(
                client.char_name, client.area.status))
            database.log_room('status', client, client.area, message=arg)
        except AreaError:
            raise


def ooc_cmd_area(client, arg):
    """
    List areas, or go to another area/room.
    Usage: /area [id] or /area [name]
    """
    args = arg.split()
    if len(args) == 0:
        client.send_area_list()
        return

    try:
        area = client.server.area_manager.get_area_by_id(int(args[0]))
        client.change_area(area)
    except:
        try:
            area = client.server.area_manager.get_area_by_name(arg)
            client.change_area(area)
        except ValueError:
            raise ArgumentError('Area ID must be a name or a number.')
        except (AreaError, ClientError):
            raise


def ooc_cmd_getarea(client, arg):
    """
    Show information about the current or another area.
    Usage: /getarea [area id]
    """
    if len(arg) == 0:
        client.send_area_info(client.area.id, False)
        return

    try:
        client.server.area_manager.get_area_by_id(int(arg[0]))
        area = int(arg[0])
        client.send_area_info(area, False)
    except ValueError:
        raise ArgumentError('Area ID must be a number.')
    except (AreaError, ClientError):
        raise


def ooc_cmd_getareas(client, arg):
    """
    Show information about all areas.
    Usage: /getareas
    """
    client.send_area_info(-1, False)


def ooc_cmd_getafk(client, arg):
    """
    Show currently AFK-ing players in the current area or in all areas.
    Usage: /getafk [all]
    """
    if arg == 'all':
        arg = -1
    elif len(arg) == 0:
        arg = client.area.id
    else:
        raise ArgumentError('There is only one optional argument [all].')
    client.send_area_info(arg, False, afk_check=True)


def ooc_cmd_area_lock(client, arg):
    """
    Prevent users from joining the current area.
    Usage: /area_lock
    """
    if not client.area.locking_allowed:
        client.send_ooc('Area locking is disabled in this area.')
    elif client.area.is_locked == client.area.Locked.LOCKED:
        client.send_ooc('Area is already locked.')
    elif client in client.area.owners or client.is_mod:
        client.area.lock()
    else:
        raise ClientError('Only CM can lock the area.')


def ooc_cmd_area_spectate(client, arg):
    """
    Allow users to join the current area, but only as spectators.
    Usage: /area_spectate
    """
    #if not client.area.locking_allowed:
        #client.send_ooc('Area locking is disabled in this area.')
    if client.area.is_locked == client.area.Locked.SPECTATABLE:
        client.send_ooc('Area is already spectatable.')
    elif client in client.area.owners or client.is_mod:
        client.area.spectator()
        database.log_room('area.spectate', client, client.area, message=None)
    else:
        raise ClientError('Only CM can make the area spectatable.')

def ooc_cmd_area_unlock(client, arg):
    """
    Allow anyone to freely join the current area.
    Usage: /area_unlock
    """
    if client.area.is_locked == client.area.Locked.FREE:
        raise ClientError('Area is already unlocked.')
    elif client in client.area.owners or client.is_mod:
        client.area.unlock()
        client.send_ooc('Area is unlocked.')
        database.log_room('area.unlock', client, client.area, message=None)
    else:
        raise ClientError('Only CM can unlock area.')

def ooc_cmd_link(client, arg):
    """
    Show a requested HTML link, a list of links or add/set a link.
    Usage: /link [choice]
    Mod usage: /link [choice]: <link>
    """
    links_list = client.server.misc_data
    max = 10

    if links_list is None:
        raise ClientError('data.yaml is null. Tell someone.')
    
    if len(arg) == 0:
        msg = 'Links available (use /link <option>):\n'
        msg += "\n".join(links_list)
        client.send_ooc(msg)
    # bit sloppy but shrug
    elif ':' in arg:
        if client.is_mod:
            args = arg.split(': ')
            args[0] = args[0].lower()
            args[0] = args[0].strip(' ')
            if args[0] in links_list:
                try:
                    client.server.misc_data[args[0]] = args[1]
                    client.server.save_miscdata()
                    client.send_ooc(f'{args[0]} set!')
                    database.log_room(f'link.set "{args[0]}"', client, client.area, message=args[1])
                except:
                    raise ArgumentError('Input error, link not set.\nUse /link <choice>: [link]')
            else:
                if len(links_list) < max:
                    if args[0].isspace() or args[0] == "":
                        raise ArgumentError('You must enter a link name.')
                    else:
                        try:
                            client.server.misc_data[args[0]] = args[1]
                            client.server.save_miscdata()
                            client.send_ooc(f'Link "{args[0]}" created and set!')
                            database.log_room(f'link.create "{args[0]}"', client, client.area, message=args[1])
                        except:
                            raise ArgumentError('Input error, link not set.\nUse /link <choice>: [link]')
                else:
                    raise ClientError('Link list is full!')
        else:
            raise ClientError('You must be authorized to do that.')
    else:
        arg = arg.lower()
        choice = arg.capitalize()
        if arg in links_list:
            try:
                if arg == 'update':
                    client.send_ooc('Latest {}: {}'.format(choice, client.server.misc_data[arg]))
                else:
                    client.send_ooc('{}: {}'.format(choice, client.server.misc_data[arg]))
                    database.log_room('link.request', client, client.area, message=arg)
            except:
                raise ClientError('Link has not been set!')
        else:
            raise ArgumentError('Link not found. Use /link to see possible choices.')

@mod_only()
def ooc_cmd_removelink(client, arg):
    """
    Remove a specific HTML link from data.
    Usage: /removelink <choice>
    """
    links_list = client.server.misc_data

    if len(arg) == 0:
        raise ArgumentError('You must specify a link to delete.')

    arg = arg.lower()
    if arg in links_list:
        try:
            del links_list[arg]
            client.server.save_miscdata()
            client.send_ooc(f'Deleted link "{arg}".')
            database.log_room('link.delete', client, client.area, message=arg)
        except:
            raise ClientError('Error, link has not been deleted.')
    else:
        raise ArgumentError('Link not found. Use /link to see possible choices.')

# Quick access to update
def ooc_cmd_update(client, arg):
    """
    See the link to the latest update.
    Usage: /update
    """
    try:
        client.send_ooc('Latest Update: {}'.format(client.server.misc_data['update']))
    except:
        raise ClientError('Update not set!')

@mod_only()
def ooc_cmd_delay(client, arg):
    """
    Change the minimum delay between messages, default is 100.
    Usage: /delay [delay]
    """
    if len(arg) == 0:
        client.area.next_message_delay = 100
    else:        
        client.area.next_message_delay = int(arg)
    
    database.log_room('delay', client, client.area, message=client.area.next_message_delay)

@mod_only(area_owners=True)
def ooc_cmd_invite(client, arg):
    """
    Allow a particular user to join a locked or spectator-only area.
    Usage: /invite <id>
    """
    if not arg:
        raise ClientError('You must specify a target. Use /invite <id>')
    elif client.area.is_locked == client.area.Locked.FREE:
        raise ClientError('Area isn\'t locked.')
    try:
        c = client.server.client_manager.get_targets(client, TargetType.ID,
                                                     int(arg), False)[0]
        if c.ipid in client.area.invite_list:
            client.send_ooc("This user has already been invited to the area!")
            return
        client.area.invite_list[c.ipid] = None
        client.send_ooc('{} is invited to your area.'.format(
            c.char_name))
        c.send_ooc(
            f'You were invited and given access to {client.area.name}.')
        database.log_room('invite', client, client.area, target=c)
    except:
        raise ClientError('You must specify a target. Use /invite <id>')


@mod_only(area_owners=True)
def ooc_cmd_uninvite(client, arg):
    """
    Revoke an invitation for a particular user.
    Usage: /uninvite <id>
    """
    if client.area.is_locked == client.area.Locked.FREE:
        raise ClientError('Area isn\'t locked.')
    elif not arg:
        raise ClientError('You must specify a target. Use /uninvite <id>')
    arg = arg.split(' ')
    targets = client.server.client_manager.get_targets(client, TargetType.ID,
                                                       int(arg[0]), True)
    if targets:
        try:
            for c in targets:
                if c.ipid not in client.area.invite_list:
                    raise ArgumentError('This user has already been uninvited from the area!')
                client.send_ooc(
                    "You have removed {} from the whitelist.".format(
                        c.char_name))
                c.send_ooc(
                    "You were removed from the area whitelist.")
                database.log_room('uninvite', client, client.area, target=c)
                if client.area.is_locked != client.area.Locked.FREE:
                    client.area.invite_list.pop(c.ipid)
        except AreaError:
            raise
        except ClientError:
            raise
    else:
        client.send_ooc("No targets found.")


@mod_only()
def ooc_cmd_area_kick(client, arg):
    """
    Remove a user from the current area and move them to another area.
    If no area id is entered, user will be kicked to area 0.
    Usage: /area_kick <id> [area id]
    Special cases:
    - "afk" area kicks all users set to /afk.
    """
    if not arg:
        raise ClientError(
            'You must specify a target. Use /area_kick <id> [area id]')
    arg = arg.split(' ')
    if arg[0].lower() == 'afk':
        trgtype = TargetType.AFK
        argi = arg[0]
    else:
        trgtype = TargetType.ID
        argi = int(arg[0])
    
    targets = client.server.client_manager.get_targets(client, trgtype,
                                                       argi, False)
    if targets:
        try:
            for c in targets:
                if len(arg) == 1:
                    area = client.server.area_manager.get_area_by_id(int(0))
                    output = 0
                else:
                    try:
                        area = client.server.area_manager.get_area_by_id(
                            int(arg[1]))
                        output = arg[1]
                    except AreaError:
                        raise
                client.send_ooc(
                    "Attempting to kick {} to area {}.".format(
                        c.char_name, output))
                c.change_area(area)
                c.send_ooc(
                    f"You were kicked from the area to area {output}.")
                database.log_room('area_kick', client, client.area, target=c, message=output)
                if client.area.is_locked != client.area.Locked.FREE:
                    client.area.invite_list.pop(c.ipid)
        except AreaError:
            raise
        except ClientError:
            raise
    else:
        client.send_ooc("No targets found.")
