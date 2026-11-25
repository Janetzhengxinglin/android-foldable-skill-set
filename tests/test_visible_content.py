import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'skills'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


common = module('visible_common', ROOT / 'android-foldable-design-guidelines/scripts/common.py')
annotations = module('visible_annotations', ROOT / 'android-foldable-adaptation-review/scripts/validate_figma_annotations.py')


class VisibleContentTests(unittest.TestCase):
    def test_embedded_text_checks_reach_all_visible_containers(self):
        _, rules, _ = common.bundle()
        kinds = ['media', 'card', 'navigation', 'list', 'overlay', 'other']
        page = {'id': 'a', 'context_id': 'inner', 'components': [
            {'id': kind, 'kind': kind} for kind in kinds]}
        tasks = common.tasks({}, {'inner': {}}, {'a': page}, rules,
                             {'profile': 'screenshot-only', 'page_ids': ['a']})
        for kind in kinds:
            self.assertIn('text.composition::component::' + kind, tasks)
        self.assertNotIn('window.state::page::a', tasks)

    def test_same_page_scroll_preserves_every_source(self):
        pages = {pid: {'context_id': 'inner', 'logical_page_id': 'application'}
                 for pid in ('top', 'middle', 'bottom')}
        issue = {'locations': [{'page_id': pid} for pid in pages],
                 'presentation_groups': [{'id': 'body', 'representative_page_id': 'top',
                                          'covered_page_ids': list(pages), 'reason': 'same object'}]}
        self.assertEqual(len(common.presentation_groups(issue, pages)), 1)
        issue['presentation_groups'][0]['covered_page_ids'].pop()
        with self.assertRaises(ValueError):
            common.presentation_groups(issue, pages)

    def test_padding_keeps_semantic_target_and_rejects_displaced_box(self):
        semantic = [951, 135, 9, 88]
        mapping = {'annotation_bbox_px': [935, 127, 41, 104],
                   'annotation_reason': 'clearance around narrow evidence'}
        self.assertEqual(annotations.annotation_box(mapping, semantic), [935, 127, 41, 104])
        self.assertEqual(semantic, [951, 135, 9, 88])
        for box in ([950, 127, 9, 104], [800, 127, 200, 104]):
            with self.assertRaises(ValueError):
                annotations.annotation_box({**mapping, 'annotation_bbox_px': box}, semantic)

    def test_unpadded_legacy_mapping_remains_valid(self):
        semantic = [100, 100, 80, 40]
        self.assertEqual(annotations.annotation_box({}, semantic), semantic)
        with self.assertRaises(ValueError):
            annotations.annotation_box({'annotation_bbox_px': [92, 92, 96, 56]}, semantic)


if __name__ == '__main__':
    unittest.main()
