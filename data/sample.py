# Create an OpenFF Molecule object from the ligand SDF fiel
from openforcefield.topology import Molecule
from openforcefield.typing.engines.smirnoff import ForceField
from simtk.openmm.app import PDBFile
import parmed
from simtk.openmm import app
from simtk.openmm.app import NoCutoff, HBonds
from simtk import unit
from simtk.openmm import XmlSerializer
from simtk import openmm
import time
import os 
import parmed

print(dir(parmed))
if  not os.path.exists('complex.xml') or not os.path.exists('complex.pdb'):
    print('1: loading Ligand molecule')
    ligand_off_molecule = Molecule('ligand.sdf')

    # Load the SMIRNOFF-format Parsley force field

    #force_field = ForceField('openff_unconstrained-1.0.0.offxml')
    print("2: Loading the Force Field")
    force_field = ForceField('openff_unconstrained-1.2.0.offxml')


    # Parametrize the ligand molecule by creating a Topology object from it
    print("3: Create Ligand System")
    ligand_system = force_field.create_openmm_system(ligand_off_molecule.to_topology())
    # Read in the coordinates of the ligand from the PDB file
    ligand_pdbfile = PDBFile('ligand.pdb')

    # Convert OpenMM System object containing ligand parameters into a ParmEd Structure.
    print("4: Transforming Ligand System to Parmed")
    ligand_structure = parmed.openmm.load_topology(ligand_pdbfile.topology,
                                                    ligand_system,
                                                    xyz=ligand_pdbfile.positions)

    print("5: Loading the protein pdb file")
    receptor_pdbfile = PDBFile('receptor.pdb')

    # Load the AMBER protein force field through OpenMM.
    omm_forcefield = app.ForceField('amber14-all.xml')

    # Parameterize the protein.
    print("6: Create protein system")
    receptor_system = omm_forcefield.createSystem(receptor_pdbfile.topology)

    # Convert the protein System into a ParmEd Structure.
    print("7: Convert protein system to parmed")
    receptor_structure = parmed.openmm.load_topology(receptor_pdbfile.topology,
                                                    receptor_system,
                                                    xyz=receptor_pdbfile.positions)

    print("8: Combinding protein & ligand system")
    complex_structure = receptor_structure + ligand_structure

    print(dir(complex_structure))
    print("9: Create Openmm system")
    # Convert the Structure to an OpenMM System in vacuum.
    complex_system = complex_structure.createSystem(nonbondedMethod=NoCutoff,
                                                    nonbondedCutoff=9.0*unit.angstrom,
                                                    constraints=HBonds,
                                                    removeCMMotion=False)

    complex_structure.save('complex.pdb', overwrite=True)
    complex_structure=parmed.load_file('complex.pdb')
    with open('complex.xml', 'w') as f:
        f.write(XmlSerializer.serialize(complex_system))

complex_structure=parmed.load_file('complex.pdb')

with open('complex.xml', 'r') as f:
    complex_system=XmlSerializer.deserialize(f.read())


print(dir(complex_structure))
platform = openmm.Platform.getPlatformByName('OpenCL')
properties = {'OpenCLPrecision': 'mixed'}
integrator = openmm.LangevinIntegrator(300*unit.kelvin,91/unit.picosecond, 0.002*unit.picoseconds)
simulation = openmm.app.Simulation(complex_structure, complex_system, integrator,platform)
simulation.context.setPositions(complex_structure.positions)
print("     starting minimization")
state = simulation.context.getState(getEnergy=True, getForces=True)
lastEnergy=state.getPotentialEnergy()
print('     Starting pot energy:', state.getPotentialEnergy())
t0=time.time()
iterations=1
for i in range(100):
    simulation.minimizeEnergy(tolerance=0, maxIterations=1)
    state = simulation.context.getState(getPositions=True, getEnergy=True)
    currentEnergy=state.getPotentialEnergy()
    print(dir(currentEnergy))
    if(abs(lastEnergy-currentEnergy)<100):
        iterations=100
    else:
        iterations=1
    lastEnergy=currentEnergy
    print('     Current pot energy:', currentEnergy)
    #simulation.context.setPositions(complex_structure.positions)
        
state = simulation.context.getState(getPositions=True, getEnergy=True, getForces=True)
print('     Final pot energy:', state.getPotentialEnergy())
print("       in ",time.time()-t0)
