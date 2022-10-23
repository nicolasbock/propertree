# Copyright 2021 Edward Hope-Morley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import yaml

from unittest import mock

from . import utils

from structr import (
    StructROverrideBase,
    StructRMappedOverrideBase,
    StructRSection,
)


class StructRCustomOverrideBase(StructROverrideBase):
    pass


class StructRInput(StructRCustomOverrideBase):

    @classmethod
    def _override_keys(cls):
        return ['input']


class StructRMessage(StructROverrideBase):

    @classmethod
    def _override_keys(cls):
        return ['message', 'message-alt']

    def __str__(self):
        return self.content


class StructRMeta(StructROverrideBase):

    @classmethod
    def _override_keys(cls):
        return ['meta']


class StructRSettings(StructROverrideBase):

    @classmethod
    def _override_keys(cls):
        return ['settings']

    @property
    def a_property(self):
        return "i am a property"


class StructRAction(StructROverrideBase):

    @classmethod
    def _override_keys(cls):
        return ['action', 'altaction']


class StructRRaws(StructROverrideBase):

    @classmethod
    def _override_keys(cls):
        return ['raws']


class StructRMappedGroupBase(StructRMappedOverrideBase):

    @classmethod
    def _override_mapped_member_types(cls):
        return [StructRSettings, StructRAction]

    @property
    def all(self):
        _all = {}
        if self.settings:
            _all['settings'] = self.settings.content

        if self.action:
            _all['action'] = self.action.content

        return _all


class StructRMappedGroupLogicalOpt(StructRMappedGroupBase):

    @classmethod
    def _override_keys(cls):
        return ['and', 'or', 'not']


class StructRMappedGroup(StructRMappedGroupBase):

    @classmethod
    def _override_keys(cls):
        return ['group']

    @classmethod
    def _override_mapped_member_types(cls):
        return super()._override_mapped_member_types() + \
                    [StructRMappedGroupLogicalOpt]


class StructRMappedRefsBase(StructRMappedOverrideBase):

    @classmethod
    def _override_mapped_member_types(cls):
        # has no members
        return []


class StructRMappedRefsLogicalOpt(StructRMappedRefsBase):

    @classmethod
    def _override_keys(cls):
        return ['and', 'or', 'not']


class StructRMappedRefs(StructRMappedRefsBase):

    @classmethod
    def _override_keys(cls):
        return ['refs']

    @classmethod
    def _override_mapped_member_types(cls):
        return super()._override_mapped_member_types() + \
                    [StructRMappedRefsLogicalOpt]


class TestStructR(utils.BaseTestCase):

    def test_struct(self):
        overrides = [StructRInput, StructRMessage, StructRSettings,
                     StructRMeta]
        with open('examples/checks.yaml') as fd:
            root = StructRSection('fruit tastiness', yaml.safe_load(fd.read()),
                                  override_handlers=overrides)
            for leaf in root.leaf_sections:
                self.assertEqual(leaf.meta.category, 'tastiness')
                self.assertEqual(leaf.root.name, 'fruit tastiness')
                self.assertEqual(leaf.input.type, 'dict')
                if leaf.parent.name == 'apples':
                    if leaf.name == 'tasty':
                        self.assertEqual(str(leaf.message),
                                         'they make good cider.')
                        self.assertIsNone(leaf.message_alt, None)
                        self.assertEqual(leaf.input.value,
                                         {'color': 'red', 'crunchiness': 15})
                        self.assertEqual(leaf.settings.crunchiness,
                                         {'operator': 'ge', 'value': 10})
                        self.assertEqual(leaf.settings.color,
                                         {'operator': 'eq', 'value': 'red'})
                    else:
                        self.assertEqual(str(leaf.message),
                                         'default message')
                        self.assertIsNone(leaf.message_alt, None)
                        self.assertEqual(leaf.input.value,
                                         {'color': 'brown', 'crunchiness': 0})
                        self.assertEqual(leaf.settings.crunchiness,
                                         {'operator': 'le', 'value': 5})
                        self.assertEqual(leaf.settings.color,
                                         {'operator': 'eq', 'value': 'brown'})
                else:
                    self.assertEqual(str(leaf.message),
                                     'they make good juice.')
                    self.assertEqual(str(leaf.message_alt),
                                     'and good marmalade.')
                    self.assertEqual(leaf.input.value,
                                     {'acidity': 2, 'color': 'orange'})
                    self.assertEqual(leaf.settings.acidity,
                                     {'operator': 'lt', 'value': 5})
                    self.assertEqual(leaf.settings.color,
                                     {'operator': 'eq', 'value': 'red'})

    def test_empty_struct(self):
        overrides = [StructRInput, StructRMessage, StructRSettings]
        root = StructRSection('root', content={}, override_handlers=overrides)
        for leaf in root.leaf_sections:
            self.assertEqual(leaf.input.type, 'dict')

    def test_struct_w_mapping(self):
        with open('examples/checks2.yaml') as fd:
            root = StructRSection('atest', yaml.safe_load(fd.read()),
                                  override_handlers=[StructRMessage,
                                                     StructRMappedGroup])
            for leaf in root.leaf_sections:
                self.assertTrue(leaf.name in ['item1', 'item2', 'item3',
                                              'item4', 'item5'])
                if leaf.name == 'item1':
                    self.assertEqual(type(leaf.group), StructRMappedGroup)
                    self.assertEqual(len(leaf.group), 1)
                    self.assertEqual(leaf.group.settings.plum, 'pie')
                    self.assertEqual(leaf.group.action.eat, 'now')
                    self.assertEqual(leaf.group.all,
                                     {'settings': {'plum': 'pie'},
                                      'action': {'eat': 'now'}})
                elif leaf.name == 'item2':
                    self.assertEqual(leaf.group.settings.apple, 'tart')
                    self.assertEqual(leaf.group.action.eat, 'later')
                    self.assertEqual(leaf.group.all,
                                     {'settings': {'apple': 'tart'},
                                      'action': {'eat': 'later'}})
                elif leaf.name == 'item3':
                    self.assertEqual(str(leaf.message), 'message not mapped')
                    self.assertEqual(leaf.group.settings.ice, 'cream')
                    self.assertEqual(leaf.group.action, None)
                    self.assertEqual(leaf.group.all,
                                     {'settings': {'ice': 'cream'}})
                elif leaf.name == 'item4':
                    self.assertEqual(leaf.group.settings.treacle, 'tart')
                    self.assertEqual(leaf.group.action.want, 'more')
                    self.assertEqual(leaf.group.all,
                                     {'settings': {'treacle': 'tart'},
                                      'action': {'want': 'more'}})
                elif leaf.name == 'item5':
                    self.assertEqual(len(leaf.group), 3)
                    checked = 0
                    for i, _group in enumerate(leaf.group):
                        if i == 0:
                            checked += 1
                            self.assertEqual(_group.settings.strawberry,
                                             'jam')
                            self.assertEqual(_group.action.lots, 'please')
                        elif i == 1:
                            checked += 1
                            self.assertEqual(_group.settings.cherry, 'jam')
                            self.assertEqual(_group.action.lots, 'more')
                        elif i == 2:
                            checked += 1
                            self.assertEqual(_group.settings.cherry, 'jam')
                            self.assertEqual(_group.action.lots, 'more')
                            self.assertEqual(_group.altaction.still, 'more')

                    self.assertEqual(checked, 3)

    def test_struct_w_metagroup_list(self):
        _yaml = """
        item1:
          group:
            - settings:
                result: true
            - settings:
                result: false
        """
        root = StructRSection('mgtest', yaml.safe_load(_yaml),
                              override_handlers=[StructRMappedGroup])
        for leaf in root.leaf_sections:
            self.assertEqual(len(leaf.group), 1)
            self.assertEqual(len(leaf.group.settings), 2)
            results = [s.result for s in leaf.group.settings]

        self.assertEqual(results, [True, False])

    def test_struct_w_metagroup_w_logical_opt(self):
        _yaml = """
        item1:
          group:
            and:
              - settings:
                  result: true
              - settings:
                  result: false
        """
        root = StructRSection('mgtest', yaml.safe_load(_yaml),
                              override_handlers=[StructRMappedGroup])
        for leaf in root.leaf_sections:
            self.assertEqual(len(leaf.group), 1)
            self.assertEqual(len(getattr(leaf.group, 'and').settings), 2)
            results = [s.result for s in getattr(leaf.group, 'and').settings]

        self.assertEqual(results, [True, False])

    def test_struct_w_metagroup_w_multiple_logical_opts(self):
        _yaml = """
        item1:
          group:
            or:
              - settings:
                  result: true
              - settings:
                  result: false
            and:
              settings:
                result: false
        """
        root = StructRSection('mgtest', yaml.safe_load(_yaml),
                              override_handlers=[StructRMappedGroup])
        for leaf in root.leaf_sections:
            self.assertEqual(len(leaf.group), 1)
            self.assertEqual(len(getattr(leaf.group, 'and').settings), 1)
            self.assertEqual(len(getattr(leaf.group, 'or').settings), 2)
            results = [s.result for s in getattr(leaf.group, 'and').settings]
            self.assertEqual(results, [False])
            results = [s.result for s in getattr(leaf.group, 'or').settings]

        self.assertEqual(results, [True, False])

    def test_struct_w_metagroup_w_mixed_list(self):
        _yaml = """
        item1:
          group:
            - or:
                settings:
                  result: true
            - settings:
                result: false
        """
        root = StructRSection('mgtest', yaml.safe_load(_yaml),
                              override_handlers=[StructRMappedGroup])
        for leaf in root.leaf_sections:
            self.assertEqual(len(leaf.group), 1)
            self.assertEqual(len(getattr(leaf.group, 'or').settings), 1)
            self.assertEqual(len(getattr(leaf.group, 'or')), 1)
            results = []
            for groupitem in leaf.group:
                for item in groupitem:
                    if item._override_name == 'or':
                        for settings in item:
                            for entry in settings:
                                results.append(entry.result)
                    else:
                        for settings in item:
                            results.append(settings.result)

        self.assertEqual(sorted(results), sorted([True, False]))

    def test_struct_w_metagroup_w_mixed_list_w_str_overrides(self):
        _yaml = """
        item1:
          refs:
            - or: ref1
              and: [ref2, ref3]
            - ref4
        """
        root = StructRSection('mgtest', yaml.safe_load(_yaml),
                              override_handlers=[StructRMappedRefs])
        results = []
        for leaf in root.leaf_sections:
            self.assertEqual(leaf.name, 'item1')
            for refs in leaf.refs:
                for item in refs:
                    self.assertTrue(item._override_name in ['and', 'or',
                                                            'ref4'])
                    if item._override_name == 'or':
                        self.assertEqual(len(item), 1)
                        for subitem in item.members:
                            results.append(subitem._override_name)
                    elif item._override_name == 'and':
                        self.assertEqual(len(item), 1)
                        for subitem in item.members:
                            results.append(subitem._override_name)
                    else:
                        results.append(item._override_name)

        self.assertEqual(sorted(results),
                         sorted(['ref1', 'ref2', 'ref3', 'ref4']))

    @mock.patch.object(StructRSection, 'post_hook')
    @mock.patch.object(StructRSection, 'pre_hook')
    def test_hooks_called(self, mock_pre_hook, mock_post_hook):
        _yaml = """
        myroot:
          leaf1:
            settings:
              brake: off
          leaf2:
            settings:
              clutch: on
        """
        StructRSection('hooktest', yaml.safe_load(_yaml),
                       override_handlers=[StructRMappedGroup],
                       run_hooks=False)
        self.assertFalse(mock_pre_hook.called)
        self.assertFalse(mock_post_hook.called)

        StructRSection('hooktest', yaml.safe_load(_yaml),
                       override_handlers=[StructRMappedGroup],
                       run_hooks=True)
        self.assertTrue(mock_pre_hook.called)
        self.assertTrue(mock_post_hook.called)

    def test_resolve_paths(self):
        _yaml = """
        myroot:
          sub1:
            sub2:
              leaf1:
                settings:
                  brake: off
                action: go
              leaf2:
                settings:
                  clutch: on
          sub3:
            leaf3:
              settings:
                clutch: on
        """
        root = StructRSection('resolvtest', yaml.safe_load(_yaml),
                              override_handlers=[StructRMappedGroup])
        resolved = []
        for leaf in root.leaf_sections:
            resolved.append(leaf.resolve_path)
            resolved.append(leaf.group._override_path)
            for setting in leaf.group.members:
                resolved.append(setting._override_path)

        expected = ['resolvtest.myroot.sub1.sub2.leaf1',
                    'resolvtest.myroot.sub1.sub2.leaf1.group',
                    'resolvtest.myroot.sub1.sub2.leaf1.group.settings',
                    'resolvtest.myroot.sub1.sub2.leaf1.group.action',
                    'resolvtest.myroot.sub1.sub2.leaf2',
                    'resolvtest.myroot.sub1.sub2.leaf2.group',
                    'resolvtest.myroot.sub1.sub2.leaf2.group.settings',
                    'resolvtest.myroot.sub3.leaf3',
                    'resolvtest.myroot.sub3.leaf3.group',
                    'resolvtest.myroot.sub3.leaf3.group.settings']

        self.assertEqual(resolved, expected)

    def test_context(self):
        _yaml = """
        myroot:
          leaf1:
            settings:
              brake: off
        """

        class ContextHandler(object):
            def __init__(self):
                self.context = {}

            def set(self, key, value):
                self.context[key] = value

            def get(self, key):
                return self.context.get(key)

        root = StructRSection('contexttest', yaml.safe_load(_yaml),
                              override_handlers=[StructRMappedGroup],
                              context=ContextHandler())
        for leaf in root.leaf_sections:
            for setting in leaf.group.members:
                self.assertIsNone(setting.context.get('k1'))
                setting.context.set('k1', 'notk2')
                self.assertEqual(setting.context.get('k1'), 'notk2')

    def test_raw_types(self):
        _yaml = """
        raws:
          red: meat
          bits: 8
          bytes: 1
          stringbits: '8'
        """
        root = StructRSection('rawtest', yaml.safe_load(_yaml),
                              override_handlers=[StructRRaws])
        for leaf in root.leaf_sections:
            self.assertEqual(leaf.raws.red, 'meat')
            self.assertEqual(leaf.raws.bytes, 1)
            self.assertEqual(leaf.raws.bits, 8)
            self.assertEqual(leaf.raws.stringbits, '8')
