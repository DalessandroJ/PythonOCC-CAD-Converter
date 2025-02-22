import os
import shutil
from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCC.Core.IGESControl import IGESControl_Reader, IGESControl_Writer
from OCC.Core.BRepTools import breptools
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing

def sew_shape(shape, tolerance=1e-3):
    """Attempt to sew disjoint surfaces together."""
    sewing = BRepBuilderAPI_Sewing(tolerance)
    sewing.Add(shape)
    sewing.Perform()
    return sewing.SewedShape()

def load_step(filename):
    """Loads a STEP file and returns a compound containing all shapes."""
    reader = STEPControl_Reader()
    reader.ReadFile(filename)
    reader.TransferRoots()

    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)

    for i in range(1, reader.NbRootsForTransfer() + 1):
        shape = reader.Shape(i)
        builder.Add(compound, shape)

    return compound

def load_iges(filename):
    """Loads an IGES file and returns a compound containing all shapes."""
    reader = IGESControl_Reader()
    reader.ReadFile(filename)
    reader.TransferRoots()

    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)

    for i in range(1, reader.NbRootsForTransfer() + 1):
        shape = reader.Shape(i)
        builder.Add(compound, shape)

    return compound

def convert_file(input_file, output_format, output_dir, sew=False, batch_mode=False, stl_deflection=0.1):
    """
    Converts a CAD file to the specified format.
    If the input file is already of the target format:
      - In batch mode: the file is copied (using its original name) and marked as skipped.
      - In file mode: a message is returned indicating no conversion is necessary.
    For multi-shape files, shapes are merged into a single compound.
    For STL conversion, the provided stl_deflection value is used.
    """
    ext = os.path.splitext(input_file)[1].lower()

    # Normalize input file formats
    if ext in [".step", ".stp"]:
        input_format = "step"
    elif ext in [".iges", ".igs"]:
        input_format = "iges"
    elif ext == ".brep":
        input_format = "brep"
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    # If input format equals desired output format, handle differently.
    if input_format == output_format:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        if batch_mode:
            shutil.copy2(input_file, output_file)
            return ("skipped", output_file)
        else:
            return ("message", f"No point in converting a {input_format.upper()} file to a {input_format.upper()} file.")

    # Otherwise, perform conversion.
    if input_format == "step":
        shape = load_step(input_file)
    elif input_format == "iges":
        shape = load_iges(input_file)
        if sew:
            shape = sew_shape(shape)
    elif input_format == "brep":
        builder = BRep_Builder()
        shape = TopoDS_Compound()
        builder.MakeCompound(shape)
        breptools.Read(shape, input_file, builder)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Build output file name with a suffix indicating source format
    suffix = f"_from{input_format.upper()}"
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, base_name + suffix + f".{output_format}")

    if output_format == "step":
        writer = STEPControl_Writer()
        writer.Transfer(shape, STEPControl_AsIs)
        writer.Write(output_file)
    elif output_format == "iges":
        writer = IGESControl_Writer()
        writer.AddShape(shape)
        writer.ComputeModel()
        writer.Write(output_file)
    elif output_format == "brep":
        breptools.Write(shape, output_file)
    elif output_format == "stl":
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
        from OCC.Core.StlAPI import StlAPI_Writer
        BRepMesh_IncrementalMesh(shape, stl_deflection)
        writer = StlAPI_Writer()
        writer.Write(shape, output_file)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

    return ("success", output_file)
