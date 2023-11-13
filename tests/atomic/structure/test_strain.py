# coding: utf-8
import unittest
import numpy as np
from ase.build import bulk
from structuretoolkit.analyse.strain import Strain
from pyiron_atomistics import ase_to_pyiron


class TestAtoms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        structure_bulk = ase_to_pyiron(bulk('Fe', cubic=True))
        cls.strain = Strain(structure_bulk, structure_bulk)

    def test_number_of_neighbors(self):
        self.assertEqual(self.strain.num_neighbors, 8)
        structure_bulk = ase_to_pyiron(bulk('Al', cubic=True))
        strain = Strain(structure_bulk, structure_bulk)
        self.assertEqual(strain.num_neighbors, 12)

    def test_get_angle(self):
        self.assertAlmostEqual(self.strain._get_angle([1, 0, 0], [0, 1, 1]), 0.5*np.pi)
        self.assertAlmostEqual(self.strain._get_angle([1, 0, 0], [1, 1, 0]), 0.25*np.pi)

    def test_get_perpendicular_unit_vector(self):
        a = np.random.random(3)
        self.assertTrue(np.allclose(
            self.strain._get_perpendicular_unit_vectors(a),
            self.strain._get_perpendicular_unit_vectors(a*2)
        ))
        b = np.random.random(3)
        self.assertAlmostEqual(np.sum(self.strain._get_perpendicular_unit_vectors(a, b)*b), 0)
        self.assertAlmostEqual(
            np.linalg.norm(self.strain._get_perpendicular_unit_vectors(a, b)), 1
        )

    def test_get_safe_unit_vectors(self):
        self.assertAlmostEqual(self.strain._get_safe_unit_vectors([0,0,0]).sum(), 0)

    def test_get_rotation_from_vectors(self):
        v = np.random.random(3)
        w = np.random.random(3)
        v, w = v/np.linalg.norm(v), w/np.linalg.norm(w)
        self.assertTrue(np.allclose(self.strain._get_rotation_from_vectors(v, w)@v, w))


if __name__ == "__main__":
    unittest.main()
