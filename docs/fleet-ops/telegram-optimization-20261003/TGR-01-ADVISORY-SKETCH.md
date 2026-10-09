# TGR-01 advisory implementation sketch from prior tech analysis

Provenance: native comment from tech on t_e8c66b4a (run2215); not an executed implementation and NOT acceptance evidence. Original base worktree is still clean. Only the patch sketch and fixture ideas follow. Any assertions, identifiers or proposed behavior require actual source/fixture verification against the new source spec. Use ONLY native read_file/search_files/patch/write_file for file operations; terminal only for git/tests. No denied ancillary file, no alternate spelling/glob/dynamic reading of it. The actual group identifier in the authoritative new spec is -1004426332349; positive pseudo-values in this sketch are not live configuration.

ФИКС — 3 правки (тексты сверены с диском):
A) run_config_loaders.py: заменить блок `_channel_override` (101-107) на:
```python
    def _channel_override(self, platform: Platform, chat_id: str, thread_id, parent_id, *, source=None):
        """``channel_overrides`` entry for this channel/thread, or None (also when no config is bound).

        With ``source`` (model/provider consumers) the lookup runs against the ROUTED profile's
        typed config under multiplex (``_channel_override_config_for_source``); without it the
        launch-profile lookup is unchanged (``_get_system_prompt_for_channel`` keeps its semantics).
        """
        from gateway.run import _get_channel_override
        config = (
            self._channel_override_config_for_source(source)
            if source is not None else getattr(self, "config", None)
        )
        if not config:
            return None
        return _get_channel_override(config, platform, chat_id, thread_id=thread_id, parent_id=parent_id)

    def _channel_override_config_for_source(self, source):
        """Typed config whose ``channel_overrides`` govern *source*: the ROUTED profile's (TGR-01).

        ``self.config`` is the launch profile's (under multiplex always the default root's), so a
        secondary bot's chat must not resolve its channel rules from there. The routed profile's
        typed config comes from the existing served-profile cache ``_profile_configs`` (populated
        and refreshed by ``run_adapters._start_one_profile_adapters``; the profile reconcile
        re-scan reloads it when the profile's config files change). Name resolution mirrors
        ``_resolve_profile_home_for_source``: pinned identity, ``source.profile``, then configured
        routes. The launch/primary profile keeps ``self.config``; a routed-but-unserved or unknown
        profile returns None so the lookup yields NO override and resolution falls through to the
        profile-scoped global default — never another profile's channel rules.
        """
        config = getattr(self, "config", None)
        if config is None or source is None:
            return config
        if not getattr(config, "multiplex_profiles", False):
            return config
        name = None
        try:
            from gateway.session_identity import identity_of
            identity = identity_of(source)
            if identity is not None:
                name = identity.session_key_profile
        except Exception:
            name = None
        if not name:
            name = str(getattr(source, "profile", "") or "").strip() or None
        if not name:
            # Same suppression as ``_busy_profile_name_for_source``: an unmatched/rejected route
            # means the default profile serves the turn (its rules are the safe fallback).
            try:
                name = self._profile_name_for_source(source)
            except Exception:
                name = None
        primary = str(getattr(self, "_primary_profile_name", "") or "") or "default"
        if not name or name == primary:
            return config
        configs = getattr(self, "_profile_configs", None)
        if not isinstance(configs, dict):
            return None
        return configs.get(name)

    def _channel_override_for_source(self, source):
        """``channel_overrides`` entry for *source*'s chat/thread/parent under its routed profile's
        typed config (TGR-01). Shared by the turn runtime (``_resolve_session_agent_runtime``) and
        the /model slash path (``_channel_override_for``) so both resolve the SAME rule."""
        if source is None:
            return None
        return self._channel_override(
            source.platform, str(source.chat_id) if source.chat_id else "",
            str(source.thread_id) if getattr(source, "thread_id", None) else None,
            str(source.parent_chat_id) if getattr(source, "parent_chat_id", None) else None,
            source=source,
        )
```
Плюс в `_resolve_model_for_channel` (109-...): добавить kw-only `source: Any = None` в сигнатуру и передать `source=source` в вызов `self._channel_override(platform, chat_id, thread_id, parent_id, source=source)`.

B) run_turn.py `_resolve_session_agent_runtime`: в from-import списке gateway.run убрать `_get_channel_override` (остальные четыре имени оставить); заменить блок
```python
        cfg = getattr(self, "config", None)  # getattr: bare object.__new__ test runners
        if cfg and source is not None:
            ch = _get_channel_override(
                cfg, source.platform, str(source.chat_id) if source.chat_id else "",
                thread_id=str(source.thread_id) if getattr(source, "thread_id", None) else None,
                parent_id=str(source.parent_chat_id) if getattr(source, "parent_chat_id", None) else None,
            )
```
на
```python
        # TGR-01: the channel override comes from the ROUTED profile's typed config — self.config
        # is the launch profile's (under multiplex: the default root's), so reading it here forced
        # a secondary bot's chat onto the launch profile's channel rules (or none) instead of its
        # own. ``_channel_override_for_source`` uses the served-profile config cache; unknown or
        # unserved profiles yield no override (global default), never another profile's rules.
        if source is not None:
            ch = self._channel_override_for_source(source)
```
Тело `if ch:` (model/provider + ch_runtime_model) не меняется.

C) slash_commands_model.py `_channel_override_for` (369-375) — заменить тело на делегирование:
```python
    def _channel_override_for(self, source):
        """This chat's ``channel_overrides`` entry (model/provider), or None — resolved against the
        ROUTED profile's typed config under multiplex via the shared gateway helper (TGR-01)."""
        return self._channel_override_for_source(source)
```

ТЕСТЫ: новый файл tests/gateway/test_profile_channel_override_routing.py — 14 тестов, харнесс как в test_channel_overrides.py (object.__new__(GatewayRunner); runner.config = GatewayConfig(multiplex_profiles=True, platforms={TELEGRAM: PlatformConfig(enabled=True, channel_overrides=...)}); runner._session_model_overrides={}; runner._primary_profile_name="default"; runner._profile_configs={...}). Моки: patch gateway.run._resolve_gateway_model → "sol/6.1", gateway.run._resolve_runtime_agent_kwargs → nous-рантайм, gateway.run._resolve_runtime_agent_kwargs_for_provider → side_effect с логом (provider, target_model) и custom-рантаймом. Матрица:
RED на base (через существующие точки входа): (1) company DM fresh → model qwen3.8-max, runtime provider custom, base_url custom, лог вызовов [("custom","qwen3.8-max")]; (2) forum thread-20 правило → то же; (3) fresh topic 21 наследует forum-level правило company; (4) identity-pin: setattr(source, "_identity", RoutingIdentity(transport_profile="product", runtime_profile="company", authorization_home/runtime_home=Path(...))) → правила company (SessionSource НЕ frozen); (5) specialist product в том же форуме → собственное правило astral/petrichor, не qwen; (6) product без правила → global sol/6.1, вызовов провайдера нет; (7) unserved "ghost" + launch-правило на этот чат → global, НИКАКИХ launch-правил (два варианта раннера: с _profile_configs и без атрибута); (8) warm signature: resolve → sig1 = GatewayRunner._agent_config_signature(model, rt, [], ""); подмена _profile_configs["company"] на Sol-правило; resolve → sig2; assert sig1 != sig2; (9) slash: runner._channel_override_for(source) → овerride company (model+provider); (10) runner._resolve_model_for_channel(TELEGRAM, dm, user_config=..., source=...) → qwen3.8-max (на base RED как TypeError).
GREEN-гарды (проходят и на base): (11) default-source (profile=None) → launch-правило; (12) multiplex=False + stale profile="company" → launch-правило; (13) session-pin: runner._session_state(skey).conversation.model_override = {"model": "sol/6.1-pinned", "provider": "nous", "api_key": "***", base_url/api_mode, + пустой dict в pool-ключе (тогда fast path не зовёт реальный pool-резолвер)} → pin побеждает channel-правило, лог вызовов пуст; (14) scope-гард: _get_system_prompt_for_channel остаётся на launch-конфиге (Launch prompt, не Company prompt).
Константы топологии из спеки: COMPANY_DM="1256122537", COMPANY_FORUM="1004426332349", QWEN_MODEL="qwen3.8-max", GLOBAL_MODEL="sol/6.1".

