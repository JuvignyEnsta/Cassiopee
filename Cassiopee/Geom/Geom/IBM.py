"""Immersed boundary geometry definition module.
"""
import Converter.PyTree as C
import Converter.Internal as Internal
import numpy
import copy
import Generator.IBMmodelHeight as G_IBM_Height
from . import PyTree as D
varsDeleteIBM = ['utau','StagnationEnthalpy','StagnationPressure',
                'dirx'          ,'diry'          ,'dirz',
                'gradxPressure' ,'gradyPressure' ,'gradzPressure' ,
                'gradxVelocityX','gradyVelocityX','gradzVelocityX',
                'gradxVelocityY','gradyVelocityY','gradzVelocityY',
                'gradxVelocityZ','gradyVelocityZ','gradzVelocityZ',
                'KCurv'         ,'yplus']        
#==============================================================================
# Creation of a case with a symmetry plane
#==============================================================================
def _symetrizePb(t, bodySymName, snear_sym, dir_sym=2):
    base = Internal.getNodeFromName(t, bodySymName)
    _symetrizeBody(base, dir_sym=dir_sym)
    _addSymPlane(t, snear_sym, dir_sym=dir_sym)
    return None

def _symetrizeBody(base, dir_sym=2):
    import Transform.PyTree as T
    zones = Internal.getZones(base)
    C._initVars(zones,'centers:cellN',1.)
    if dir_sym == 2:
        v1 = (1,0,0); v2=(0,0,1)
    elif dir_sym == 1:
        v1 = (0,1,0); v2=(0,0,1)
    elif dir_sym == 3:
        v1 = (1,0,0); v2=(0,1,0)

    zones_dup = T.symetrize(zones,(0,0,0),v1, v2)
    for z in zones_dup: z[0] += '_sym'
    T._reorder(zones_dup,(-1,2,3))
    C._initVars(zones_dup,'centers:cellN',0.)
    base[2]+= zones_dup
    return None

def _addSymPlane(tb, snear_sym, dir_sym=2):
    import Generator.PyTree as G
    snearList=[]; dfarList=[]
    snearFactor=50
    bodies = Internal.getZones(tb)
    for nos, s in enumerate(bodies):
        sdd = Internal.getNodeFromName1(s, ".Solver#define")
        snearl = Internal.getNodeFromName1(sdd, "snear")
        if snearl is not None:
            snearl = Internal.getValue(snearl)
            snearList.append(snearl*snearFactor)
        
        dfarl = Internal.getNodeFromName1(sdd,"dfar")
        if dfarl is not None:
            dfarl = Internal.getValue(dfarl)
            dfarList.append(dfarl)

    o = G.octree(tb, snearList=snearList, dfarList=dfarList)

    [xmin,ymin,zmin,xmax,ymax,zmax] = G.bbox(o)
    L = 0.5*(xmax+xmin); eps = 0.2*L
    xmin = xmin-eps; ymin = ymin-eps; zmin = zmin-eps
    xmax = xmax+eps; ymax = ymax+eps; zmax = zmax+eps
    if dir_sym==1: coordsym = 'CoordinateX'; xmax=0
    elif dir_sym==2: coordsym = 'CoordinateY'; ymax=0
    elif dir_sym==3: coordsym = 'CoordinateZ'; zmax=0
    a = D.box((xmin,ymin,zmin),(xmax,ymax,zmax))
    C._initVars(a,'{centers:cellN}=({centers:%s}>-1e-8)'%coordsym)
    C._addBase2PyTree(tb,"SYM")
    base = Internal.getNodeFromName(tb,"SYM"); base[2]+=a
    _setSnear(base,snear_sym)
    _setDfar(base,-1.)
    _setIBCType(base, "slip")
    return None
#==============================================================================
# compute the near wall spacing in agreement with the yplus target at image points - front42
#==============================================================================
def computeSnearOpt(Re=None, tb=None, Lref=1., q=1.2, yplus=300., Cf_law='ANSYS'):
    return G_IBM_Height.computeSnearOpt(Re=Re, tb=tb, Lref=Lref, q=q, yplus=yplus, Cf_law=Cf_law)

#==============================================================================
# Set snear in zones
#==============================================================================
def setSnear(t, value):
    """Set the value of snear in a geometry tree.
    Usage: setSnear(t, value=X)"""
    tp = Internal.copyRef(t)
    _setSnear(tp, value)
    return tp


def _setSnear(t, value):
    """Set the value of snear in a geometry tree.
    Usage: _setSnear(t,value=X)"""
    zones = Internal.getZones(t)
    for z in zones:
        Internal._createUniqueChild(z, '.Solver#define', 'UserDefinedData_t')
        n = Internal.getNodeFromName1(z, '.Solver#define')
        Internal._createUniqueChild(n, 'snear', 'DataArray_t', float(value))
    return None

#==============================================================================
# Set dfar in zones
#==============================================================================
def setDfar(t, value):
    """Set the value of dfar in a geometry tree.
    Usage: setDfar(t, value=X)"""
    tp = Internal.copyRef(t)
    _setDfar(tp, value)
    return tp


def _setDfar(t, value):
    """Set the value of dfar in a geometry tree.
        Usage: _setDfar(t, value=X)"""
    zones = Internal.getZones(t)
    for z in zones:
        Internal._createUniqueChild(z, '.Solver#define', 'UserDefinedData_t')
        n = Internal.getNodeFromName1(z, '.Solver#define')
        Internal._createUniqueChild(n, 'dfar', 'DataArray_t', float(value))
    return None

#==============================================================================
#
#==============================================================================
def getDfarOpt(tb, vmin, snear_opt, factor=10, nlevel=-1):
    """Computes the optimal dfar to get the exact snear.
    Usage: getDfarOpt(tb, vmin, snear_opt, factor=10, nlevel=-1)"""
    import Generator.PyTree as G
    bb = G.bbox(tb)
    sizemax = max(bb[3]-bb[0],bb[4]-bb[1],bb[5]-bb[2])
    #print('sizemax',sizemax)
    if factor>0 and nlevel <1:
        dfar= factor*sizemax
        nlevel = int(numpy.ceil((numpy.log(2*dfar+sizemax)-numpy.log((vmin-1)*snear_opt))/numpy.log(2)))
        #print('nb levels=',nlevel)
    elif nlevel > 0:
        pass
    dfaropt = 0.5*(snear_opt*(2**nlevel*(vmin-1)) - sizemax)
    dfaropt = numpy.trunc(dfaropt*10**nlevel)/10**nlevel
    #print('dfar opt',dfaropt)
    #print('2*dfar opt + sizemax =',2*dfar + sizemax)
    #print('2**n*vmin*snear opt =',(vmin-1)*snear_opt*2**nlevel)
    return dfaropt

#==============================================================================
# Multiply the snear by factors XX in zones
#==============================================================================
def snearFactor(t, sfactor):
    """Multiply the value of snear in a geometry tree by a sfactor.
    Usage: snearFactor(t, sfactor)"""
    tp = Internal.copyRef(t)
    _snearFactor(tp, sfactor)
    return tp


def _snearFactor(t, sfactor):
    """Multiply the value of snear in a geometry tree by a sfactor.
    Usage: _snearFactor(t, sfactor)"""
    zones = Internal.getZones(t)
    for z in zones:
        nodes = Internal.getNodesFromName2(z, 'snear')
        for n in nodes:
            Internal._setValue(n, sfactor*Internal.getValue(n))
    return None

#==============================================================================
# Set the IBC type in zones
#==============================================================================
def setIBCType(t, value):
    """Set the IBC type in a geometry tree.
    Usage: setIBCType(t, value=X)"""
    tp = Internal.copyRef(t)
    _setIBCType(tp, value)
    return tp


def _setIBCType(t, value):
    """Set the IBC type in a geometry tree.
    Usage: _setIBCType(t, value=X)"""
    zones = Internal.getZones(t)
    for z in zones:         
        Internal._createUniqueChild(z, '.Solver#define', 'UserDefinedData_t')
        n = Internal.getNodeFromName1(z, '.Solver#define')
        Internal._createUniqueChild(n, 'ibctype', 'DataArray_t', value)
    return None

#==============================================================================
# Set the fluid inside the geometry
#==============================================================================
def setFluidInside(t):
    """Set fluid inside a geometry tree.
    Usage: setFluidInside(t)"""
    tp = Internal.copyRef(t)
    _setFluidInside(tp)
    return tp

def _setFluidInside(t):
    """Set fluid inside a geometry tree.
    Usage: _setFluidInside(t)"""
    zones = Internal.getZones(t)
    for z in zones:
        Internal._createUniqueChild(z, '.Solver#define', 'UserDefinedData_t')
        n = Internal.getNodeFromName1(z, '.Solver#define')
        Internal._createUniqueChild(n, 'inv', 'DataArray_t', value=1)
    return None

#==============================================================================
# Set outpress control parameters in zones
#==============================================================================
def setOutPressControlParam(t, probeName='pointOutPress', AtestSection=1, AOutPress=1,
                            machTarget=0.1, pStatTarget=1e05, tStatTarget=298.15,lmbd=0.1,
                            cxSupport = 0.6, sSupport=0.1):
    """Set the user input parameters for the outpress control algorithm.
    Usage: setOutPressControlParam(t, probeName='X', AtestSection=Y, AOutPress=Z, machTarget=XX,pStatTarget=YY,tStatTarget=ZZ,lmbd=XXX,cxSupport=YYY,sSupport=ZZZ)"""
    tp = Internal.copyRef(t)
    _setOutPressControlParam(tp, probeName=probeName, AtestSection=AtestSection, AOutPress=AOutPress,
                             machTarget=machTarget, pStatTarget=pStatTarget, tStatTarget=tStatTarget,lmbd=lmbd,
                             cxSupport = cxSupport, sSupport=sSupport)
    return tp


def _setOutPressControlParam(t, probeName='pointOutPress', AtestSection=1, AOutPress=1,
                             machTarget=0.1, pStatTarget=1e05, tStatTarget=298.15,lmbd=0.1,
                             cxSupport = 0.6, sSupport=0.1):
    """Set the user input parameters for the outpress control algorithm.
    Usage: _setOutPressControlParam(t, probeName='X', AtestSection=Y, AOutPress=Z, machTarget=XX,pStatTarget=YY,tStatTarget=ZZ,lmbd=XXX,cxSupport=YYY,sSupport=ZZZ)"""
    zones = Internal.getZones(t)
    for z in zones:
        Internal._createUniqueChild(z, '.Solver#define', 'UserDefinedData_t')
        n = Internal.getNodeFromName1(z, '.Solver#define')
        Internal._createUniqueChild(n, 'probeName'   , 'DataArray_t', probeName)
        Internal._createUniqueChild(n, 'AtestSection', 'DataArray_t', AtestSection)
        Internal._createUniqueChild(n, 'AOutPress'   , 'DataArray_t', AOutPress)
        Internal._createUniqueChild(n, 'machTarget'  , 'DataArray_t', machTarget)
        Internal._createUniqueChild(n, 'pStatTarget' , 'DataArray_t', pStatTarget)
        Internal._createUniqueChild(n, 'tStatTarget' , 'DataArray_t', tStatTarget)
        Internal._createUniqueChild(n, 'lmbd'        , 'DataArray_t', lmbd)
        Internal._createUniqueChild(n, 'cxSupport'   , 'DataArray_t', cxSupport)
        Internal._createUniqueChild(n, 'sSupport'    , 'DataArray_t', sSupport)
        
    return None
#==============================================================================
# Set the IBC type outpress for zones in familyName
#==============================================================================
def initOutflow(tc, familyName, PStatic, InterpolPlane=None, PressureVar=0, isDensityConstant=True):
    """Set the value of static pressure PStatic for the outflow pressure IBC with family name familyName. 
    A plane InterpolPlane may also be provided with only static pressure variable or various variables with static pressure as the PressureVar (e.g. 2nd) variable)"""
    tc2 = Internal.copyRef(tc)
    _initOutflow(tc2, familyName, PStatic, InterpolPlane=InterpolPlane, PressureVar=PressureVar, isDensityConstant=isDensityConstant)
    return tc2

def _initOutflow(tc, familyName, PStatic, InterpolPlane=None, PressureVar=0, isDensityConstant=True):
    """Set the value of the pressure PStatic for the outflow pressure IBC with family name familyName.
    A plane InterpolPlane may also be provided with various variables with static pressure as the PressureVar (e.g. 2nd) variable)"""
    import Post.PyTree as P
    for zc in Internal.getZones(tc):
        for zsr in Internal.getNodesFromName(zc, 'IBCD_4_*'):
            FamNode = Internal.getNodeFromType1(zsr, 'FamilyName_t')
            if FamNode is not None:
                FamName = Internal.getValue(FamNode)
                if FamName == familyName:
                    stagPNode = Internal.getNodeFromName(zsr, 'Pressure')
                    sizeIBC = numpy.shape(stagPNode[1])
                    if InterpolPlane:
                        print("Zone: %s | ZoneSubRegion: %s"%(zc[0],zsr[0]))
                        x_wall = Internal.getNodeFromName(zsr, 'CoordinateX_PW')[1]
                        y_wall = Internal.getNodeFromName(zsr, 'CoordinateY_PW')[1]
                        z_wall = Internal.getNodeFromName(zsr, 'CoordinateZ_PW')[1]
                        list_pnts = []
                        for i in range(sizeIBC[0]): list_pnts.append((x_wall[i],y_wall[i],z_wall[i]))
                        val = P.extractPoint(InterpolPlane, list_pnts, 2)
                        val_flat = []
                        for i in range(len(val)): val_flat.append(val[i][PressureVar])
                        stagPNode[1][:] = val_flat[:]
                    else:
                        stagPNode[1][:] = PStatic
                    if not isDensityConstant:
                        dens = Internal.getNodeFromName(zsr, 'Density') 
                        dens[1][:] = -dens[1][:]
    return None

#==============================================================================
# 
#==============================================================================
def initIsoThermal(tc, familyName, TStatic):
    """Set the value of static temperature TStatic for the wall no slip IBC with family name familyName.
    Usage: initIsoThermal(tc, familyName, TStatic)"""
    tc2 = Internal.copyRef(tc)
    _initIsoThermal(tc2, familyName, TStatic)
    return tc2

def _initIsoThermal(tc, familyName, TStatic):
    """Set the value of static temperature TStatic for the wall no slip IBC with family name familyName.
    Usage: _initIsoThermal(tc, familyName, TStatic)"""
    for zc in Internal.getZones(tc):
        for zsr in Internal.getNodesFromName(zc, 'IBCD_12_*'):
            FamNode = Internal.getNodeFromType1(zsr, 'FamilyName_t')
            if FamNode is not None:
                FamName = Internal.getValue(FamNode)
                if FamName == familyName:
                    stagPNode = Internal.getNodeFromName(zsr, 'TemperatureWall')    
                    sizeIBC = numpy.shape(stagPNode[1])
                    stagPNode[1][:] = TStatic
                    #Internal.setValue(stagPNode,TStatic*numpy.ones(sizeIBC))

                    stagPNode = Internal.getNodeFromName(zsr, 'Temperature')    
                    Internal.setValue(stagPNode, TStatic*numpy.ones(sizeIBC))
    return None

#==============================================================================
# 
#==============================================================================
def initHeatFlux(tc, familyName, QWall):
    """Set the value of heat flux QWall for the wall no slip IBC with family name familyName.
    Usage: initHeatFlux(tc,familyName, QWall)"""
    tc2 = Internal.copyRef(tc)
    _initHeatFlux(tc2, familyName, QWall)
    return tc2


def _initHeatFlux(tc, familyName, QWall):
    """Set the value of heat flux QWall for the wall no slip IBC with family name familyName.
    Usage: _initHeatFlux(tc,familyName, QWall)"""
    for zc in Internal.getZones(tc):
        for zsr in Internal.getNodesFromName(zc,'IBCD_13_*'):
            FamNode = Internal.getNodeFromType1(zsr,'FamilyName_t')
            if FamNode is not None:
                FamName = Internal.getValue(FamNode)
                if FamName == familyName:
                    stagPNode = Internal.getNodeFromName(zsr,'WallHeatFlux')    
                    sizeIBC   = numpy.shape(stagPNode[1])
                    stagPNode[1][:]  = QWall
                    #Internal.setValue(stagPNode,QWall*numpy.ones(sizeIBC))

                    stagPNode =  Internal.getNodeFromName(zsr,'Temperature')    
                    Internal.setValue(stagPNode,QWall*numpy.ones(sizeIBC))
    return None

#==============================================================================
# Set the IBC type inj for zones in familyName
#==============================================================================
def initInj(tc, familyName, PTot, HTot, injDir=[1.,0.,0.], InterpolPlane=None, PressureVar=0, EnthalpyVar=0):
    """Set the total pressure PTot, total enthalpy HTot, and direction of the flow injDir for the injection IBC with family name familyName.
    A plane InterpolPlane may also be provided with at least the stagnation pressure and stagnation enthalpy variables with the former and latter as the PressureVar (e.g. 2nd) and EnthalpyVar variables, respectively.)
    Usage: initInj(tc, familyName, PTot, HTot, injDir, InterpolPlane, PressureVar, EnthalpyVar)"""
    tc2 = Internal.copyRef(tc)
    _initInj(tc2, familyName, PTot, HTot, injDir, InterpolPlane=InterpolPlane, PressureVar=PressureVar, EnthalpyVar=EnthalpyVar)
    return tc2
                 

def _initInj(tc, familyName, PTot, HTot, injDir=[1.,0.,0.], InterpolPlane=None, PressureVar=0, EnthalpyVar=0):
    """Set the total pressure PTot, total enthalpy HTot, and direction of the flow injDir for the injection IBC with family name familyName.
    A plane InterpolPlane may also be provided with at least the stagnation pressure and stagnation enthalpy variables with the former and latter as the PressureVar (e.g. 2nd) and EnthalpyVar variables, respectively.)
    Usage: _initInj(tc, familyName, PTot, HTot, injDir, InterpolPlane, PressureVar, EnthalpyVar)"""
    import Post.PyTree as P
    for zc in Internal.getZones(tc):
        for zsr in Internal.getNodesFromName(zc, 'IBCD_5_*'):
            FamNode = Internal.getNodeFromType1(zsr, 'FamilyName_t')
            if FamNode is not None:
                FamName = Internal.getValue(FamNode)
                if FamName == familyName:
                    node_temp = Internal.getNodeFromName(zsr, 'utau')
                    if node_temp is not None: Internal._rmNode(zsr, node_temp)

                    node_temp = Internal.getNodeFromName(zsr, 'yplus')
                    if node_temp is not None: Internal._rmNode(zsr, node_temp)
                    
                    stagPNode = Internal.getNodeFromName(zsr, 'StagnationPressure')
                    stagHNode = Internal.getNodeFromName(zsr, 'StagnationEnthalpy')
                    dirxNode  = Internal.getNodeFromName(zsr, 'dirx')
                    diryNode  = Internal.getNodeFromName(zsr, 'diry')
                    dirzNode  = Internal.getNodeFromName(zsr, 'dirz')
                    sizeIBC   = numpy.shape(stagHNode[1])
                    if InterpolPlane:
                        print("Zone: %s | ZoneSubRegion: %s"%(zc[0],zsr[0]))
                        x_wall = Internal.getNodeFromName(zsr, 'CoordinateX_PW')[1]
                        y_wall = Internal.getNodeFromName(zsr, 'CoordinateY_PW')[1]
                        z_wall = Internal.getNodeFromName(zsr, 'CoordinateZ_PW')[1]
                        list_pnts=[]
                        for i in range(sizeIBC[0]): list_pnts.append((x_wall[i],y_wall[i],z_wall[i]))
                        val = P.extractPoint(InterpolPlane, list_pnts, 2)
                        val_flatPtot = []
                        val_flatHtot = []
                        for i in range(len(val)):
                            val_flatPtot.append(val[i][PressureVar])
                            val_flatHtot.append(val[i][EnthalpyVar])
                        stagPNode[1][:] = val_flatPtot[:]
                        stagHNode[1][:] = val_flatHtot[:]
                    else:
                        stagPNode[1][:] = PTot
                        stagHNode[1][:] = HTot
                    dirxNode[1][:] = injDir[0]
                    diryNode[1][:] = injDir[1]
                    dirzNode[1][:] = injDir[2]
                    
    return None

#==============================================================================
# Add variables to the IBC
#==============================================================================
def _addVariablesTcIbc(zsr, ibctype, nIBC):
    Nlength = numpy.zeros((nIBC),numpy.float64)
    if ibctype in [2, 3, 6, 10, 11]:
        zsr[2].append(['utau' , copy.copy(Nlength), [], 'DataArray_t'])
        zsr[2].append(['yplus', copy.copy(Nlength), [], 'DataArray_t'])

    if ibctype == 5:
        Internal._createChild(zsr, 'StagnationEnthalpy', 'DataArray_t', value=copy.copy(Nlength))
        Internal._createChild(zsr, 'StagnationPressure', 'DataArray_t', value=copy.copy(Nlength))
        Internal._createChild(zsr, 'dirx'              , 'DataArray_t', value=copy.copy(Nlength))
        Internal._createChild(zsr, 'diry'              , 'DataArray_t', value=copy.copy(Nlength))
        Internal._createChild(zsr, 'dirz'              , 'DataArray_t', value=copy.copy(Nlength))

    elif ibctype == 10 or ibctype == 11:
        zsr[2].append(['gradxPressure' , copy.copy(Nlength) , [], 'DataArray_t'])
        zsr[2].append(['gradyPressure' , copy.copy(Nlength) , [], 'DataArray_t'])
        zsr[2].append(['gradzPressure' , copy.copy(Nlength) , [], 'DataArray_t'])

        if ibctype == 11:
            zsr[2].append(['gradxVelocityX' , copy.copy(Nlength) , [], 'DataArray_t'])
            zsr[2].append(['gradyVelocityX' , copy.copy(Nlength) , [], 'DataArray_t'])
            zsr[2].append(['gradzVelocityX' , copy.copy(Nlength) , [], 'DataArray_t'])
            
            zsr[2].append(['gradxVelocityY' , copy.copy(Nlength) , [], 'DataArray_t'])
            zsr[2].append(['gradyVelocityY' , copy.copy(Nlength) , [], 'DataArray_t'])
            zsr[2].append(['gradzVelocityY' , copy.copy(Nlength) , [], 'DataArray_t'])
            
            zsr[2].append(['gradxVelocityZ' , copy.copy(Nlength) , [], 'DataArray_t'])
            zsr[2].append(['gradyVelocityZ' , copy.copy(Nlength) , [], 'DataArray_t'])
            zsr[2].append(['gradzVelocityZ' , copy.copy(Nlength) , [], 'DataArray_t'])
        
    elif ibctype == 100:
        zsr[2].append(["KCurv" , copy.copy(Nlength) , [], 'DataArray_t'])
        
    return None

#==============================================================================
# 
#==============================================================================
def changeIBCType(tc, oldIBCType, newIBCType):
    """Change the IBC type in a connectivity tree from oldIBCType to newIBCType.
    Usage: changeIBCType(tc, oldIBCType, newIBCType)"""
    tcp = Internal.copyRef(tc)
    _changeIBCType(tcp, oldIBCType, newIBCType)
    return tcp


def _changeIBCType(tc, oldIBCType, newIBCType):
    """Change the IBC type in a connectivity tree from oldIBCType to newIBCType.
    Usage: changeIBCType(tc, oldIBCType, newIBCType)"""
    for z in Internal.getZones(tc):
        subRegions = Internal.getNodesFromType1(z, 'ZoneSubRegion_t')
        for zsr in subRegions:
            nameSubRegion = zsr[0]
            if nameSubRegion[:4] == "IBCD":
                ibcType = int(nameSubRegion.split("_")[1])
                if ibcType == oldIBCType:
                    zsr[0] = "IBCD_{}_".format(newIBCType)+"_".join(nameSubRegion.split("_")[2:])
                    pressure = Internal.getNodeFromName(zsr, 'Pressure')[1]
                    nIBC = pressure.shape[0]

                    for var_local in varsDeleteIBM:
                        Internal._rmNodesByName(zsr, var_local)
                    
                    _addVariablesTcIbc(zsr, newIBCType, nIBC)

    return None

#==============================================================================
# 
#==============================================================================
def transformTc2(tc2):
    """Change the name of the IBM nodes for the second image point.
    Usage: transformTc2(tc2)"""
    tcp = Internal.copyRef(tc2)
    _transformTc2(tcp)
    return tcp


def _transformTc2(tc2):
    for z in Internal.getZones(tc2):
        subRegions = Internal.getNodesFromType1(z, 'ZoneSubRegion_t')
        for zsr in subRegions:
            nameSubRegion = zsr[0]
            if nameSubRegion[:6] == "2_IBCD":
                ibctype = int(nameSubRegion.split("_")[2])
                zsr[0] = "IBCD_{}_".format(ibctype)+"_".join(nameSubRegion.split("_")[3:])

                pressure = Internal.getNodeFromName(zsr, 'Pressure')[1]
                nIBC = pressure.shape[0]
                
                vars_delete = ['Density','VelocityX','VelocityY','VelocityZ']+varsDeleteIBM
                for var_local in vars_delete:
                    Internal._rmNodesByName(zsr, var_local)

                Nlength = numpy.zeros((nIBC),numpy.float64)
                zsr[2].append(['Density'   , copy.copy(Nlength) , [], 'DataArray_t'])
                zsr[2].append(['VelocityX' , copy.copy(Nlength) , [], 'DataArray_t'])
                zsr[2].append(['VelocityY' , copy.copy(Nlength) , [], 'DataArray_t'])
                zsr[2].append(['VelocityZ' , copy.copy(Nlength) , [], 'DataArray_t'])
                _addVariablesTcIbc(zsr,ibctype,nIBC)
                
    return None


