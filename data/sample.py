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

datapath='data/'

async def run(io):
    print(dir(parmed))
    if  not os.path.exists(datapath+'complex.xml') or not os.path.exists(datapath+'complex.pdb'):
        print('1: loading Ligand molecule')
        ligand_off_molecule = Molecule(datapath+'ligand.sdf')

        # Load the SMIRNOFF-format Parsley force field

        #force_field = ForceField('openff_unconstrained-1.0.0.offxml')
        print("2: Loading the Force Field")
        force_field = ForceField('openff_unconstrained-1.2.0.offxml')


        # Parametrize the ligand molecule by creating a Topology object from it
        print("3: Create Ligand System")
        ligand_system = force_field.create_openmm_system(ligand_off_molecule.to_topology())
        # Read in the coordinates of the ligand from the PDB file
        ligand_pdbfile = PDBFile(datapath+'ligand.pdb')

        # Convert OpenMM System object containing ligand parameters into a ParmEd Structure.
        print("4: Transforming Ligand System to Parmed")
        ligand_structure = parmed.openmm.load_topology(ligand_pdbfile.topology,
                                                        ligand_system,
                                                        xyz=ligand_pdbfile.positions)

        print("5: Loading the protein pdb file")
        receptor_pdbfile = PDBFile(datapath+'receptor.pdb')

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

        complex_structure.save(datapath+'complex.pdb', overwrite=True)
        complex_structure=parmed.load_file(datapath+'complex.pdb')
        with open(datapath+'complex.xml', 'w') as f:
            f.write(XmlSerializer.serialize(complex_system))

    complex_structure=parmed.load_file(datapath+'complex.pdb')

    with open(datapath+'complex.xml', 'r') as f:
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
    potEnergyValue=state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
    m = '     Starting pot energy: {:.3f} kJ/mol'.format(potEnergyValue)
    print(m)
    await io.emit("setMessage", m)
    # io.emit("setMessage", m)
    t0=time.time()
    emit_freq = 1
    maxIter = 20
    # iterations=1
    for i in range(100):
        simulation.minimizeEnergy(tolerance=0, maxIterations=maxIter)
        state = simulation.context.getState(getPositions=True, getEnergy=True)
        currentEnergy=state.getPotentialEnergy()
        positions = state.getPositions(asNumpy=True)*10 #convert to angstroms
        p = positions._value.flatten().tolist()
        # if(abs(lastEnergy._value-currentEnergy._value)<100):
        #     m ='     Last pot energy:'+ currentEnergy.__str__()+ " step: {}".format(i+1)
        #     await io.emit("setPositions", {'positions':p, 'message':m})
        #     break
            
        lastEnergy=currentEnergy
        #print("positions", p[0], p[1], p[2])
        m ='     Current pot energy: {:.3f} kJ/mol - step: {:d}'.format(currentEnergy.value_in_unit(unit.kilojoules_per_mole) ,i+1)
        #print(m)
        if not (i+1) % emit_freq: 
            await io.emit("setPositions", {'positions':p, 'message':m,'step':i})
            # io.emit("setPositions", {'positions':p, 'message':m})
            # await io.emit("setEnergy", m)
        #simulation.context.setPositions(complex_structure.positions)
            
    state = simulation.context.getState(getPositions=True, getEnergy=True, getForces=True)
    print('     Final pot energy:', state.getPotentialEnergy())
    print("       in ",time.time()-t0)
    return state
