Lattice is a set of bake tasks geared towards building set of software 
  components which comprise a software stack, or "product".  The product is 
  defined via a yaml file, and consumed by the profile assemble task.

  Components are built and installed to a build area representing the root of 
  the runtime filesystem, availble at build time as $BUILDPATH.  Components'
  individual build scripts leverage this tree to define the build time 
  dependencies that are required.  
  
  Order matters in the profile.  If a component depends on another at build time
  it must be defined above the dependent component.

lattice/ 
  tasks/
    profile.py       <- contains main profile assemble bake task
    component.py     <- component assemble bake task
    rpm.py           <- packaging post task for rpm
    deb.py           <- package post task for deb
  support/
    repository.py    <- providers for source repositories

