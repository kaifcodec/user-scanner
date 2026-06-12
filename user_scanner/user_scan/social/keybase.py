from user_scanner.core.orchestrator import generic_validate, Result

def validate_keybase(user):
    url = f"https://keybase.io/_/api/1.0/user/lookup.json?usernames={user}"
    show_url = f"https://keybase.io/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                them = data.get('them', [])
                if them and them[0] is not None:
                    user_data = them[0]
                    extra = {}
                    
                    basics = user_data.get('basics', {})
                    if basics.get('ctime'):
                        extra['created_at'] = basics.get('ctime')
                    if basics.get('id_version'):
                        extra['id_version'] = basics.get('id_version')
                        
                    profile = user_data.get('profile', {})
                    if profile.get('full_name'):
                        extra['full_name'] = profile.get('full_name')
                    if profile.get('location'):
                        extra['location'] = profile.get('location')
                    if profile.get('bio'):
                        extra['bio'] = profile.get('bio')
                        
                    proofs = user_data.get('proofs_summary', {}).get('all', [])
                    if proofs:
                        linked = []
                        for proof in proofs:
                            if proof.get('nametag'):
                                linked.append(f"{proof.get('proof_type')}:{proof.get('nametag')}")
                        if linked:
                            extra['proofs'] = ", ".join(linked)

                    return Result.taken(extra=extra)
                else:
                    return Result.available()
            except Exception:
                pass
        
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
