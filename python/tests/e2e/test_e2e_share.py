

def test_share_complete_lifecycle(run):
    captured = run(['share', 'storage:shared-read', 'public', 'read'])
    assert captured.out.strip() == 'Resource shared.'
    # TODO: Add revoke here

